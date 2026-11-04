#!/usr/bin/env python3

import os
import logging
import html
import subprocess
import secrets
import shutil
from functools import wraps
from werkzeug.utils import secure_filename
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, send_file, after_this_request
)
import ipaddress

app = Flask(__name__)

# Configuration, etc
config_file = 'app.cfg'
if not os.path.exists(config_file):
    raise FileNotFoundError(f"Critical Error: Configuration file '{config_file}' is missing.")
app.config.from_pyfile(config_file)
required_keys = ["ADMIN_MANAGED_DIR", "ALLOWED_SUBNETS", "SECRET_KEY_PATH"]
missing_keys = [key for key in required_keys if key not in app.config]
if missing_keys:
    raise RuntimeError(f"Critical Error: Missing keys in '{config_file}': {', '.join(missing_keys)}")
secret_key_path = app.config["SECRET_KEY_PATH"]
if os.path.exists(secret_key_path):
    with open(secret_key_path, "r") as f:
        app.secret_key = f.read().strip()
else:
    app.secret_key = secrets.token_hex(32)
    os.makedirs(os.path.dirname(secret_key_path), exist_ok=True)
    with open(secret_key_path, "w") as f:
        f.write(app.secret_key)
    os.chmod(secret_key_path, 0o600)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AdminPanel")

# Sanitize text.  
def sanitize_text(val):
    if val is None:
        return ""
    return html.escape(str(val).strip())

# I want IP, Give me Ip.  
def get_client_ip():
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    return request.remote_addr

# Only allow access on the UR Network.  
@app.before_request
def restrict_ip():
    client_ip_str = get_client_ip()
    try:
        client_ip = ipaddress.ip_address(client_ip_str)
        allowed_subnets = app.config.get("ALLOWED_SUBNETS", [])
        if not any(client_ip in subnet for subnet in allowed_subnets):
            logger.warning(f"Unauthorized access attempt from IP: {client_ip_str}")
            return "Access Denied: Restricted network.", 403
    except ValueError:
        return "Invalid IP address.", 400

# Auths against korvax, or some other server that is SSH-able, due to 389 and 636 not being accessible from the 167.  
def authenticate_admin_via_script(username, password):
    script_path = os.path.join(app.root_path, "scripts/check_admin.sh")
    if not os.path.exists(script_path):
        logger.error(f"Script not found at {script_path}")
        return False, "Failed to check, or not an admin"
    try:
        result = subprocess.run(
            [script_path, username],
            input=password,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, "Authentication successful."
        else:
            err_msg = result.stderr.strip() or "Failed to check, or not an admin"
            return False, err_msg
    except subprocess.TimeoutExpired:
        return False, "Failed to check, or not an admin"
    except Exception as e:
        logger.error(f"Error running authentication script: {e}")
        return False, "Failed to check, or not an admin"

# need to be logged in to access most things.  
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in_admin'):
            flash("Please log in to access the panel.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Default route.  
@app.route('/')
def index():
    if session.get('logged_in_admin'):
        return redirect(url_for('nfs_add'))
    return redirect(url_for('login'))

# login route.  
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = sanitize_text(request.form.get('username'))
        password = request.form.get('password', '')
        success, msg = authenticate_admin_via_script(username, password)
        if success:
            session['logged_in_admin'] = username
            flash("Logged in successfully!", "success")
            return redirect(url_for('nfs_add'))
        else:
            flash(msg, "error")
    return render_template('login.html')

#Logout route.  
@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

# This is pretty much just copied from panel.  
@app.route('/nfs-add', methods=['GET', 'POST'])
@login_required
def nfs_add():
    base_dir = os.path.realpath(app.config['ADMIN_MANAGED_DIR'])
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
    subpath = request.args.get('path', '').strip().lstrip('/')
    target_dir = os.path.realpath(os.path.join(base_dir, subpath))
    if not target_dir.startswith(base_dir):
        flash("Invalid path traversal attempt.", "error")
        return redirect(url_for('nfs_add'))
    if request.method == 'POST' and 'file' in request.files:
        files = request.files.getlist('file')
        upload_subpath = sanitize_text(request.form.get('current_path', '')).strip().lstrip('/')
        upload_target = os.path.realpath(os.path.join(base_dir, upload_subpath))
        if not upload_target.startswith(base_dir):
            flash("Invalid upload path.", "error")
            return redirect(url_for('nfs_add', path=subpath))
        success_count = 0
        for file in files:
            if file and file.filename:
                path_parts = file.filename.replace('\\', '/').split('/')
                secure_parts = [secure_filename(p) for p in path_parts if p and p != '..']
                if not secure_parts:
                    continue
                rel_file_path = os.path.join(*secure_parts)
                file_abs_path = os.path.realpath(os.path.join(upload_target, rel_file_path))
                if not file_abs_path.startswith(base_dir):
                    continue
                try:
                    os.makedirs(os.path.dirname(file_abs_path), exist_ok=True)
                    file.save(file_abs_path)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to save file {file.filename}: {e}")
        if success_count > 0:
            flash(f"Successfully uploaded {success_count} item(s)!", "success")
        else:
            flash("No valid files were uploaded.", "error")
        return redirect(url_for('nfs_add', path=upload_subpath))
    delete_rel_path = request.args.get('delete')
    if delete_rel_path:
        del_target = os.path.realpath(os.path.join(base_dir, delete_rel_path))
        if del_target.startswith(base_dir) and del_target != base_dir:
            try:
                if os.path.isdir(del_target):
                    shutil.rmtree(del_target)
                else:
                    os.remove(del_target)
                flash(f"Successfully deleted '{os.path.basename(delete_rel_path)}'", "success")
            except Exception as e:
                flash(f"Failed to delete: {str(e)}", "error")
        else:
            flash("Invalid deletion target.", "error")
        return redirect(url_for('nfs_add', path=subpath))
    file_list = []
    try:
        with os.scandir(target_dir) as entries:
            for entry in entries:
                if entry.name.startswith('.tmp_'):
                    continue
                item_rel_path = os.path.join(subpath, entry.name) if subpath else entry.name
                if entry.is_dir():
                    file_list.append({
                        'name': entry.name,
                        'type': 'Directory',
                        'size': '-',
                        'path': item_rel_path,
                        'is_dir': True
                    })
                elif entry.is_file():
                    try:
                        size_bytes = entry.stat().st_size
                        size_str = f"{size_bytes} bytes" if size_bytes < 1024 else f"{size_bytes // 1024} KB"
                    except Exception:
                        size_str = "Unknown"
                    file_list.append({
                        'name': entry.name,
                        'type': 'File',
                        'size': size_str,
                        'path': item_rel_path,
                        'is_dir': False
                    })
        file_list.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    except Exception as e:
        logger.error(f"Error reading directory: {e}")
        flash("Could not read directory contents.", "error")
    parent_path = ''
    if subpath:
        parent_path = os.path.dirname(subpath)
        if parent_path == '.':
            parent_path = ''

    return render_template('manage_files.html', files=file_list, current_path=subpath, parent_path=parent_path, admin_managed_dir=base_dir)

# The download route.  This is what allows users to download files... 
@app.route('/nfs-download')
@login_required
def nfs_download():
    base_dir = os.path.realpath(app.config['ADMIN_MANAGED_DIR'])
    rel_path = request.args.get('path', '')
    target_path = os.path.realpath(os.path.join(base_dir, rel_path))
    if not target_path.startswith(base_dir) or target_path == base_dir:
        flash("Invalid download target.", "error")
        return redirect(url_for('nfs_add'))
    if os.path.isfile(target_path):
        directory = os.path.dirname(target_path)
        filename = os.path.basename(target_path)
        return send_from_directory(directory, filename, as_attachment=True)
    elif os.path.isdir(target_path):
        folder_name = os.path.basename(target_path) or "directory"
        temp_dir = os.path.join(base_dir, '.tmp_downloads')
        try:
            os.makedirs(temp_dir, exist_ok=True)
            archive_base = os.path.join(temp_dir, f"{folder_name}_{os.getpid()}")
            archive_file = shutil.make_archive(archive_base, 'zip', target_path)
            @after_this_request
            def cleanup(response):
                try:
                    if os.path.exists(archive_file):
                        os.remove(archive_file)
                except Exception as e:
                    logger.error(f"Failed to clean up temp zip: {e}")
                return response
            return send_file(archive_file, as_attachment=True, download_name=f"{folder_name}.zip")
        except Exception as e:
            logger.error(f"Failed to create directory archive: {e}")
            flash(f"Failed to zip directory: {str(e)}", "error")
            return redirect(url_for('nfs_add'))
    flash("Target path does not exist.", "error")
    return redirect(url_for('nfs_add'))

if __name__ == '__main__':
    print("Starting Minutes Portal")
    print(f"Managed Directory : {app.config['ADMIN_MANAGED_DIR']}")
    app.run(host='0.0.0.0', port=5001, debug=True)

#!/bin/bash

# This is the script to check if the user is an Admin or not.    

USERNAME="$1"
read -r PASSWORD

# For our purposes, must be on the 167
USERADD_HOST="###.###.###.###"
USERADD_USER="admin_check"
USERADD_KEY="/minutes/PRIVATE/KEY"
LOG_FILE="/minutes/log.log"

log_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}


if [ -z "$USERNAME" ] || [ -z "PASSWORD" ]; then
    echo "$(log_timestamp) - FAILED: Missing username or password" >> "$LOG_FILE"
    echo "Missing required arguments: username, password" >&2
    exit 1
fi

ssh -q -o StrictHostKeyChecking=no -i "$USERADD_KEY" "$USERADD_USER@$USERADD_HOST" \
    "/home_local/admin_check/check_admin.sh -u '$USERNAME' -p '$PASSWORD'"  >/dev/null 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "$(log_timestamp) - FAILED: '$USERNAME' attempted to log in, but is not an admin " >> "$LOG_FILE"
    echo "Failed to check, or not an admin" >&2
    exit $EXIT_CODE
fi

echo "$(log_timestamp) - SUCCESS: '$USERNAME' logged in sucessfully" >> "$LOG_FILE"
exit 0

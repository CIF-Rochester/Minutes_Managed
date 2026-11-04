#!/bin/bash

# To check if a user is an admin

# Options, etc
while getopts "u:p:" opt; do
  case $opt in
    u) USERNAME="$OPTARG" ;;
    p) PASSWORD="$OPTARG" ;;
    * ) echo "Usage: $0 -u username -p password" >&2; exit 2 ;;
  esac
done
if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
    echo "Error: Username and password are required." >&2
    exit 1
fi

# Check if user is valid, password correct, and if they are an admin
REALM="CIF.ROCHESTER.EDU"
if ! echo "$PASSWORD" | kinit "${USERNAME}@${REALM}" >/dev/null 2>&1; then
    echo "Authentication failed: Invalid username or password." >&2
    exit 1
fi
if ipa group-show admins | grep -qw "$USERNAME"; then
    kdestroy >/dev/null 2>&1
    exit 0
else
    echo "Access Denied: User '$USERNAME' is not an admin." >&2
    kdestroy >/dev/null 2>&1
    exit 1
fi

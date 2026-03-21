#!/usr/bin/env bash
set -euo pipefail

SMB_HOST="${SMB_HOST:-nas}"
SMB_SHARE="${SMB_SHARE:-data}"
SMB_USER="${SMB_USER:-smbuser}"
SMB_PASSWORD="${SMB_PASSWORD:-smbpass}"
SMB_MOUNT_DIR="${SMB_MOUNT_DIR:-/home/kasm-user/nas}"
SMB_VERSION="${SMB_VERSION:-3.0}"

mkdir -p /home/kasm-user
touch /home/kasm-user/.bashrc
chown -R 1000:1000 /home/kasm-user

wget -q -O /dev/null http://teamcity-server:8111 || true

mkdir -p "$SMB_MOUNT_DIR"

if ! mountpoint -q "$SMB_MOUNT_DIR"; then
  for attempt in $(seq 1 10); do
    if mount -t cifs "//${SMB_HOST}/${SMB_SHARE}" "$SMB_MOUNT_DIR" \
      -o "username=${SMB_USER},password=${SMB_PASSWORD},vers=${SMB_VERSION},uid=1000,gid=1000,file_mode=0664,dir_mode=0775"; then
      break
    fi
    sleep 2
  done
fi

exec /dockerstartup/vnc_startup.sh

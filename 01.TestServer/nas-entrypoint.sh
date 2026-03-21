#!/usr/bin/env bash
set -euo pipefail

SMB_USER="${SMB_USER:-smbuser}"
SMB_PASSWORD="${SMB_PASSWORD:-smbpass}"
SMB_SHARE_NAME="${SMB_SHARE_NAME:-data}"
SMB_READ_ONLY="${SMB_READ_ONLY:-no}"

mkdir -p /data

if ! id -u "$SMB_USER" >/dev/null 2>&1; then
  useradd -M -s /usr/sbin/nologin "$SMB_USER"
fi

echo -e "${SMB_PASSWORD}\n${SMB_PASSWORD}" | smbpasswd -a -s "$SMB_USER"

cat > /etc/samba/smb.conf <<EOF
[global]
   workgroup = WORKGROUP
   security = user
   map to guest = Bad User
   passdb backend = tdbsam
   smb ports = 445 139
   server min protocol = SMB2
   server max protocol = SMB3
   log file = /var/log/samba/log.%m
   max log size = 50
   load printers = no
   disable spoolss = yes

[${SMB_SHARE_NAME}]
   path = /data
   browseable = yes
   read only = ${SMB_READ_ONLY}
   guest ok = no
   valid users = ${SMB_USER}
   force user = ${SMB_USER}
   create mask = 0664
   directory mask = 0775
EOF

chown -R "$SMB_USER":"$SMB_USER" /data

nmbd -F --no-process-group &
exec smbd -F --no-process-group

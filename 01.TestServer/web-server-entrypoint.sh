#!/usr/bin/env bash
set -euo pipefail

mkdir -p /var/run/sshd

# Ensure sshd_config does not contain unsupported Include directive
if grep -qE '^\s*Include\s+/etc/ssh/sshd_config.d/\*\.conf' /etc/ssh/sshd_config; then
  sed -i '/^\s*Include\s\+\/etc\/ssh\/sshd_config.d\/\*\.conf/d' /etc/ssh/sshd_config
fi

ssh_config_file="/etc/ssh/sshd_config"
if grep -qE '^\s*PermitRootLogin' "$ssh_config_file"; then
  sed -i 's/^\s*PermitRootLogin.*/PermitRootLogin yes/' "$ssh_config_file"
else
  echo "PermitRootLogin yes" >> "$ssh_config_file"
fi

if [ -n "${SSH_PASSWORD:-}" ]; then
  echo "root:${SSH_PASSWORD}" | chpasswd
  if grep -qE '^\s*PasswordAuthentication' "$ssh_config_file"; then
    sed -i 's/^\s*PasswordAuthentication.*/PasswordAuthentication yes/' "$ssh_config_file"
  else
    echo "PasswordAuthentication yes" >> "$ssh_config_file"
  fi
else
  if grep -qE '^\s*PasswordAuthentication' "$ssh_config_file"; then
    sed -i 's/^\s*PasswordAuthentication.*/PasswordAuthentication no/' "$ssh_config_file"
  else
    echo "PasswordAuthentication no" >> "$ssh_config_file"
  fi
fi

if [ -n "${SSH_PUBLIC_KEY:-}" ]; then
  mkdir -p /root/.ssh
  printf "%s\n" "$SSH_PUBLIC_KEY" > /root/.ssh/authorized_keys
  chmod 700 /root/.ssh
  chmod 600 /root/.ssh/authorized_keys
  if grep -qE '^\s*PubkeyAuthentication' "$ssh_config_file"; then
    sed -i 's/^\s*PubkeyAuthentication.*/PubkeyAuthentication yes/' "$ssh_config_file"
  else
    echo "PubkeyAuthentication yes" >> "$ssh_config_file"
  fi
fi

/usr/sbin/sshd

exec catalina.sh run

#!/usr/bin/env bash
set -euo pipefail

APP_USER="${LINKVAULT_USER:-linkvault}"
APP_GROUP="${LINKVAULT_GROUP:-linkvault}"
APP_DIR="${LINKVAULT_APP_DIR:-/opt/linkvault}"
CONFIG_DIR="${LINKVAULT_CONFIG_DIR:-/etc/linkvault}"
DATA_DIR="${LINKVAULT_DATA_DIR:-/var/lib/linkvault}"
SERVICE_NAME="${LINKVAULT_SERVICE_NAME:-linkvault}"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETUP_TOKEN="${LINKVAULT_SETUP_TOKEN:-}"

export LANG=C.UTF-8
export LC_ALL=C.UTF-8

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

echo "Installing LinkVault from ${SOURCE_DIR}"

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv curl ca-certificates

"${SOURCE_DIR}/scripts/check-requirements.sh"

if ! getent group "${APP_GROUP}" >/dev/null; then
  groupadd --system "${APP_GROUP}"
fi

if ! id -u "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --gid "${APP_GROUP}" --home-dir "${APP_DIR}" --shell /usr/sbin/nologin "${APP_USER}"
fi

install -d -o "${APP_USER}" -g "${APP_GROUP}" "${APP_DIR}" "${DATA_DIR}"
install -d -o root -g root "${CONFIG_DIR}"

python3 -m venv "${APP_DIR}/.venv"
"${APP_DIR}/.venv/bin/python" -m pip install --upgrade pip
"${APP_DIR}/.venv/bin/pip" install "${SOURCE_DIR}"
chown -R "${APP_USER}:${APP_GROUP}" "${APP_DIR}" "${DATA_DIR}"

if [[ ! -f "${CONFIG_DIR}/linkvault.env" ]]; then
  if [[ -z "${SETUP_TOKEN}" ]]; then
    SETUP_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  fi
  cat > "${CONFIG_DIR}/linkvault.env" <<EOF
LINKVAULT_ADDR=0.0.0.0:3080
LINKVAULT_DATA_DIR=${DATA_DIR}
LINKVAULT_SETUP_TOKEN=${SETUP_TOKEN}
EOF
elif ! grep -q '^LINKVAULT_SETUP_TOKEN=' "${CONFIG_DIR}/linkvault.env"; then
  if [[ -z "${SETUP_TOKEN}" ]]; then
    SETUP_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  fi
  printf '\nLINKVAULT_SETUP_TOKEN=%s\n' "${SETUP_TOKEN}" >>"${CONFIG_DIR}/linkvault.env"
else
  SETUP_TOKEN="$(sed -n 's/^LINKVAULT_SETUP_TOKEN=//p' "${CONFIG_DIR}/linkvault.env" | tail -n 1)"
fi
chown root:"${APP_GROUP}" "${CONFIG_DIR}/linkvault.env"
chmod 0640 "${CONFIG_DIR}/linkvault.env"

install -m 0644 "${SOURCE_DIR}/deploy/linkvault.service" "/etc/systemd/system/${SERVICE_NAME}.service"
install -m 0755 "${SOURCE_DIR}/scripts/backup-linkvault.sh" "/usr/local/bin/backup-linkvault.sh"
install -m 0755 "${SOURCE_DIR}/scripts/restore-linkvault.sh" "/usr/local/bin/restore-linkvault.sh"
install -m 0755 "${SOURCE_DIR}/scripts/update-linkvault.sh" "/usr/local/bin/update-linkvault.sh"
install -m 0755 "${SOURCE_DIR}/scripts/linkvault-helper.sh" "/usr/local/bin/linkvault-helper"
install -m 0755 "${SOURCE_DIR}/scripts/check-requirements.sh" "/usr/local/bin/linkvault-requirements"
ln -sf /usr/local/bin/backup-linkvault.sh /usr/bin/backup-linkvault.sh
ln -sf /usr/local/bin/restore-linkvault.sh /usr/bin/restore-linkvault.sh
ln -sf /usr/local/bin/update-linkvault.sh /usr/bin/update-linkvault.sh
ln -sf /usr/local/bin/linkvault-helper /usr/bin/linkvault-helper
ln -sf /usr/local/bin/linkvault-requirements /usr/bin/linkvault-requirements

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}"

local_ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
local_port="${LINKVAULT_PORT:-3080}"

echo
echo "=================================================="
echo " LinkVault installed successfully!"
echo "=================================================="
if [[ -n "${local_ip}" ]]; then
  echo "  URL:          http://${local_ip}:${local_port}"
else
  echo "  URL:          http://<container-ip>:${local_port}"
fi
echo "  Setup token:  ${SETUP_TOKEN}"
echo "  Healthcheck:  curl http://127.0.0.1:${local_port}/healthz"
echo "  Logs:         journalctl -u ${SERVICE_NAME} -f"
echo "  Helper:       linkvault-helper"
echo "  Backup:       linkvault-helper backup"
echo "  Restore:      linkvault-helper restore"
echo "  Update:       linkvault-helper update"
echo "=================================================="

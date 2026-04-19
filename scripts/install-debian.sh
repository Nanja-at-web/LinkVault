#!/usr/bin/env bash
set -euo pipefail

APP_USER="${LINKVAULT_USER:-linkvault}"
APP_GROUP="${LINKVAULT_GROUP:-linkvault}"
APP_DIR="${LINKVAULT_APP_DIR:-/opt/linkvault}"
CONFIG_DIR="${LINKVAULT_CONFIG_DIR:-/etc/linkvault}"
DATA_DIR="${LINKVAULT_DATA_DIR:-/var/lib/linkvault}"
SERVICE_NAME="${LINKVAULT_SERVICE_NAME:-linkvault}"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export LANG=C.UTF-8
export LC_ALL=C.UTF-8

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer as root." >&2
  exit 1
fi

echo "Installing LinkVault from ${SOURCE_DIR}"

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv curl ca-certificates

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
  cat > "${CONFIG_DIR}/linkvault.env" <<EOF
LINKVAULT_ADDR=0.0.0.0:3080
LINKVAULT_DATA_DIR=${DATA_DIR}
EOF
  chmod 0644 "${CONFIG_DIR}/linkvault.env"
fi

install -m 0644 "${SOURCE_DIR}/deploy/linkvault.service" "/etc/systemd/system/${SERVICE_NAME}.service"

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}"

echo "LinkVault installed."
echo "Healthcheck: curl http://127.0.0.1:3080/healthz"

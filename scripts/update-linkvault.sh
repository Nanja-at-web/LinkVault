#!/usr/bin/env bash
set -Eeuo pipefail

APP_USER="${LINKVAULT_USER:-linkvault}"
APP_GROUP="${LINKVAULT_GROUP:-linkvault}"
APP_DIR="${LINKVAULT_APP_DIR:-/opt/linkvault}"
CONFIG_FILE="${LINKVAULT_CONFIG_FILE:-/etc/linkvault/linkvault.env}"
SERVICE_NAME="${LINKVAULT_SERVICE_NAME:-linkvault}"
SOURCE_URL="${LINKVAULT_SOURCE_URL:-https://github.com/Nanja-at-web/LinkVault.git}"
SOURCE_REF="${LINKVAULT_SOURCE_REF:-main}"
HEALTH_URL="${LINKVAULT_HEALTH_URL:-http://127.0.0.1:3080/healthz}"
WORKDIR="$(mktemp -d)"
SERVICE_WAS_ACTIVE=0

export LANG=C.UTF-8
export LC_ALL=C.UTF-8

cleanup() {
  rm -rf "${WORKDIR}"
}
trap cleanup EXIT

on_error() {
  local exit_code="$?"
  echo "LinkVault update failed with exit code ${exit_code}." >&2
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files "${SERVICE_NAME}.service" >/dev/null 2>&1; then
    systemctl daemon-reload || true
    if [[ "${SERVICE_WAS_ACTIVE}" == "1" ]]; then
      systemctl start "${SERVICE_NAME}" || true
    fi
    systemctl status "${SERVICE_NAME}" --no-pager || true
    journalctl -u "${SERVICE_NAME}" -n 100 --no-pager || true
  fi
  exit "${exit_code}"
}
trap on_error ERR

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this updater as root." >&2
  exit 1
fi

if [[ ! -d "${APP_DIR}/.venv" ]]; then
  echo "LinkVault virtualenv not found: ${APP_DIR}/.venv" >&2
  exit 1
fi

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "LinkVault config not found: ${CONFIG_FILE}" >&2
  exit 1
fi

wait_for_health() {
  for _ in {1..60}; do
    if curl -fsS "${HEALTH_URL}"; then
      echo
      return
    fi
    sleep 1
  done

  systemctl status "${SERVICE_NAME}" --no-pager || true
  journalctl -u "${SERVICE_NAME}" -n 100 --no-pager || true
  echo "LinkVault did not become healthy after update: ${HEALTH_URL}" >&2
  exit 1
}

echo "Updating LinkVault from ${SOURCE_URL} (${SOURCE_REF})"

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y git curl ca-certificates python3 python3-venv

if git clone --depth 1 --branch "${SOURCE_REF}" "${SOURCE_URL}" "${WORKDIR}/source" >/dev/null 2>&1; then
  :
else
  git clone "${SOURCE_URL}" "${WORKDIR}/source"
  git -C "${WORKDIR}/source" checkout "${SOURCE_REF}"
fi

"${WORKDIR}/source/scripts/check-requirements.sh"

if systemctl list-unit-files "${SERVICE_NAME}.service" >/dev/null 2>&1; then
  if systemctl is-active --quiet "${SERVICE_NAME}"; then
    SERVICE_WAS_ACTIVE=1
  fi
  systemctl stop "${SERVICE_NAME}" || true
fi

"${APP_DIR}/.venv/bin/python" -m pip install --upgrade pip
"${APP_DIR}/.venv/bin/pip" install --upgrade "${WORKDIR}/source"

install -m 0644 "${WORKDIR}/source/deploy/linkvault.service" "/etc/systemd/system/${SERVICE_NAME}.service"
install -m 0755 "${WORKDIR}/source/scripts/backup-linkvault.sh" "/usr/local/bin/backup-linkvault.sh"
install -m 0755 "${WORKDIR}/source/scripts/restore-linkvault.sh" "/usr/local/bin/restore-linkvault.sh"
install -m 0755 "${WORKDIR}/source/scripts/update-linkvault.sh" "/usr/local/bin/update-linkvault.sh"
install -m 0755 "${WORKDIR}/source/scripts/linkvault-helper.sh" "/usr/local/bin/linkvault-helper"
install -m 0755 "${WORKDIR}/source/scripts/check-requirements.sh" "/usr/local/bin/linkvault-requirements"
ln -sf /usr/local/bin/backup-linkvault.sh /usr/bin/backup-linkvault.sh
ln -sf /usr/local/bin/restore-linkvault.sh /usr/bin/restore-linkvault.sh
ln -sf /usr/local/bin/update-linkvault.sh /usr/bin/update-linkvault.sh
ln -sf /usr/local/bin/linkvault-helper /usr/bin/linkvault-helper
ln -sf /usr/local/bin/linkvault-requirements /usr/bin/linkvault-requirements

if getent group "${APP_GROUP}" >/dev/null; then
  chown root:"${APP_GROUP}" "${CONFIG_FILE}"
  chmod 0640 "${CONFIG_FILE}"
fi

if id -u "${APP_USER}" >/dev/null 2>&1 && getent group "${APP_GROUP}" >/dev/null; then
  chown -R "${APP_USER}:${APP_GROUP}" "${APP_DIR}"
fi

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}"
wait_for_health

echo "LinkVault update completed."

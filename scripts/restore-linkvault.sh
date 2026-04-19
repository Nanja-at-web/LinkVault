#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/linkvault-backup.tar.gz" >&2
  exit 1
fi

ARCHIVE="$1"
APP_GROUP="${LINKVAULT_GROUP:-linkvault}"
CONFIG_FILE="${LINKVAULT_CONFIG_FILE:-/etc/linkvault/linkvault.env}"
DATA_DIR="${LINKVAULT_DATA_DIR:-/var/lib/linkvault}"
DATA_FILE="${LINKVAULT_DATA:-${DATA_DIR}/linkvault.sqlite3}"
SERVICE_NAME="${LINKVAULT_SERVICE_NAME:-linkvault}"
WORKDIR="$(mktemp -d)"
STAMP="$(date -u +%Y%m%d-%H%M%S)"

cleanup() {
  rm -rf "${WORKDIR}"
}
trap cleanup EXIT

if [[ ! -f "${ARCHIVE}" ]]; then
  echo "Backup archive not found: ${ARCHIVE}" >&2
  exit 1
fi

if [[ -f "${CONFIG_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "${CONFIG_FILE}"
  set +a
  DATA_DIR="${LINKVAULT_DATA_DIR:-${DATA_DIR}}"
  DATA_FILE="${LINKVAULT_DATA:-${DATA_DIR}/linkvault.sqlite3}"
fi
DATA_DIR="$(dirname "${DATA_FILE}")"

LC_ALL=C tar -C "${WORKDIR}" -xzf "${ARCHIVE}"

if [[ ! -f "${WORKDIR}/linkvault.sqlite3" ]]; then
  echo "Backup archive does not contain linkvault.sqlite3" >&2
  exit 1
fi

if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files "${SERVICE_NAME}.service" >/dev/null 2>&1; then
  systemctl stop "${SERVICE_NAME}" || true
fi

install -d "${DATA_DIR}"
if [[ -f "${DATA_FILE}" ]]; then
  cp "${DATA_FILE}" "${DATA_FILE}.pre-restore-${STAMP}"
fi
install -m 0640 "${WORKDIR}/linkvault.sqlite3" "${DATA_FILE}"

if [[ -f "${WORKDIR}/linkvault.env" && ! -f "${CONFIG_FILE}" ]]; then
  install -d "$(dirname "${CONFIG_FILE}")"
  install -m 0640 "${WORKDIR}/linkvault.env" "${CONFIG_FILE}"
fi

if [[ -f "${CONFIG_FILE}" && "$(basename "${CONFIG_FILE}")" == "linkvault.env" ]] && getent group "${APP_GROUP}" >/dev/null; then
  chown root:"${APP_GROUP}" "${CONFIG_FILE}"
  chmod 0640 "${CONFIG_FILE}"
fi

if id -u linkvault >/dev/null 2>&1; then
  chown -R linkvault:linkvault "${DATA_DIR}"
fi

if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files "${SERVICE_NAME}.service" >/dev/null 2>&1; then
  systemctl start "${SERVICE_NAME}"
  curl -fsS http://127.0.0.1:3080/healthz
  echo
fi

echo "LinkVault restore completed."

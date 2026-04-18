#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="${LINKVAULT_CONFIG_FILE:-/etc/linkvault/linkvault.env}"
DATA_DIR="${LINKVAULT_DATA_DIR:-/var/lib/linkvault}"
DATA_FILE="${LINKVAULT_DATA:-${DATA_DIR}/linkvault.sqlite3}"
BACKUP_DIR="${LINKVAULT_BACKUP_DIR:-/var/backups/linkvault}"
STAMP="$(date -u +%Y%m%d-%H%M%S)"
WORKDIR="$(mktemp -d)"
ARCHIVE="${BACKUP_DIR}/linkvault-backup-${STAMP}.tar.gz"

cleanup() {
  rm -rf "${WORKDIR}"
}
trap cleanup EXIT

if [[ -f "${CONFIG_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "${CONFIG_FILE}"
  set +a
  DATA_DIR="${LINKVAULT_DATA_DIR:-${DATA_DIR}}"
  DATA_FILE="${LINKVAULT_DATA:-${DATA_DIR}/linkvault.sqlite3}"
fi
DATA_DIR="$(dirname "${DATA_FILE}")"

if [[ ! -f "${DATA_FILE}" ]]; then
  echo "LinkVault database not found: ${DATA_FILE}" >&2
  exit 1
fi

install -d -m 0750 "${BACKUP_DIR}"
install -d "${WORKDIR}/payload"

python3 - "${DATA_FILE}" "${WORKDIR}/payload/linkvault.sqlite3" <<'PY'
import sqlite3
import sys

source_path, backup_path = sys.argv[1], sys.argv[2]
source = sqlite3.connect(source_path)
target = sqlite3.connect(backup_path)
with target:
    source.backup(target)
target.close()
source.close()
PY

if [[ -f "${CONFIG_FILE}" ]]; then
  cp "${CONFIG_FILE}" "${WORKDIR}/payload/linkvault.env"
fi

LC_ALL=C tar -C "${WORKDIR}/payload" -czf "${ARCHIVE}" .
chmod 0640 "${ARCHIVE}"

echo "${ARCHIVE}"

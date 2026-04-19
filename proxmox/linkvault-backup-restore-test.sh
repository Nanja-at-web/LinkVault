#!/usr/bin/env bash
set -Eeuo pipefail

# Run on the Proxmox VE host against an existing LinkVault LXC.
# Usage: LINKVAULT_CTID=112 ./proxmox/linkvault-backup-restore-test.sh

APP="LinkVault"
CTID="${LINKVAULT_CTID:-${1:-}}"
SCRIPT_BASE_URL="${LINKVAULT_SCRIPT_BASE_URL:-https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main}"
SCRIPT_CACHE_BUST="${LINKVAULT_SCRIPT_CACHE_BUST:-$(date -u +%s)}"
BACKUP_SCRIPT_URL="${SCRIPT_BASE_URL}/scripts/backup-linkvault.sh?cb=${SCRIPT_CACHE_BUST}"
RESTORE_SCRIPT_URL="${SCRIPT_BASE_URL}/scripts/restore-linkvault.sh?cb=${SCRIPT_CACHE_BUST}"
HEALTH_URL="${LINKVAULT_HEALTH_URL:-http://127.0.0.1:3080/healthz}"
MARKER_ID="backup_restore_$(date -u +%Y%m%d%H%M%S)_${RANDOM}"
MARKER_URL="https://backup-restore.invalid/${MARKER_ID}"
LOG_FILE="${LINKVAULT_BACKUP_RESTORE_LOG:-/tmp/linkvault-backup-restore-test.log}"

if [[ -z "${CTID}" && "${0:-}" =~ ^[0-9]+$ ]]; then
  CTID="$0"
fi

if [[ -t 1 ]]; then
  CL="\033[m"
  GN="\033[1;92m"
  BL="\033[36m"
  RD="\033[01;31m"
else
  CL=""
  GN=""
  BL=""
  RD=""
fi

msg_info() {
  printf "%b\n" "  ${BL}[*]${CL} $1" >&2
}

msg_ok() {
  printf "%b\n" "  ${GN}[OK]${CL} $1" >&2
}

msg_error() {
  printf "%b\n" "  ${RD}[ERROR]${CL} $1" >&2
}

run_quiet() {
  local label="$1"
  shift
  msg_info "${label}"
  if "$@" >>"${LOG_FILE}" 2>&1; then
    msg_ok "${label}"
    return
  fi

  msg_error "${label}"
  echo "Last log lines from ${LOG_FILE}:" >&2
  tail -n 100 "${LOG_FILE}" >&2 || true
  exit 1
}

require_host() {
  if [[ "${EUID}" -ne 0 ]]; then
    msg_error "Run this script as root in the Proxmox VE shell."
    exit 1
  fi
  if [[ -z "${CTID}" ]]; then
    msg_error "Set LINKVAULT_CTID or pass the CTID as first argument."
    exit 1
  fi
  if ! command -v pct >/dev/null 2>&1; then
    msg_error "pct not found. This script must run on a Proxmox VE host."
    exit 1
  fi
  if ! pct status "${CTID}" >/dev/null 2>&1; then
    msg_error "CT ${CTID} does not exist."
    exit 1
  fi
}

ct_exec() {
  pct exec "${CTID}" -- "$@"
}

download_scripts() {
  run_quiet "Installing test scripts inside CT ${CTID}" ct_exec bash -lc "
    set -euo pipefail
    command -v curl >/dev/null 2>&1 || (apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y curl ca-certificates)
    curl -fsSL '${BACKUP_SCRIPT_URL}' -o /tmp/backup-linkvault.sh
    curl -fsSL '${RESTORE_SCRIPT_URL}' -o /tmp/restore-linkvault.sh
    chmod +x /tmp/backup-linkvault.sh /tmp/restore-linkvault.sh
  "
}

insert_marker() {
  run_quiet "Creating restore marker bookmark" ct_exec env MARKER_ID="${MARKER_ID}" MARKER_URL="${MARKER_URL}" /opt/linkvault/.venv/bin/python - <<'PY'
from __future__ import annotations

import os

from linkvault.config import load_config
from linkvault.store import BookmarkStore

marker_id = os.environ["MARKER_ID"]
store = BookmarkStore(load_config().data_path, metadata_fetcher=None)
store.delete(marker_id)
bookmark = store.add(
    {
        "url": os.environ["MARKER_URL"],
        "title": "LinkVault Backup Restore Marker",
        "description": "Temporary marker used by the Proxmox LXC restore smoke test.",
        "tags": "backup-restore-test",
        "collections": "System",
        "favorite": True,
        "pinned": True,
        "notes": "This bookmark must survive restore.",
    },
    enrich_metadata=False,
)
with store.connect() as connection:
    connection.execute("UPDATE bookmarks SET id = ? WHERE id = ?", (marker_id, bookmark.id))
    connection.execute("UPDATE bookmarks_fts SET bookmark_id = ? WHERE bookmark_id = ?", (marker_id, bookmark.id))
PY
}

delete_marker() {
  run_quiet "Deleting marker after backup" ct_exec env MARKER_ID="${MARKER_ID}" /opt/linkvault/.venv/bin/python - <<'PY'
from __future__ import annotations

import os

from linkvault.config import load_config
from linkvault.store import BookmarkStore

store = BookmarkStore(load_config().data_path, metadata_fetcher=None)
store.delete(os.environ["MARKER_ID"])
PY
}

marker_count() {
  ct_exec env MARKER_ID="${MARKER_ID}" /opt/linkvault/.venv/bin/python - <<'PY'
from __future__ import annotations

import os

from linkvault.config import load_config
from linkvault.store import BookmarkStore

store = BookmarkStore(load_config().data_path, metadata_fetcher=None)
print(1 if store.get(os.environ["MARKER_ID"]) else 0)
PY
}

assert_marker_count() {
  local expected="$1"
  local actual
  actual="$(marker_count)"
  if [[ "${actual}" != "${expected}" ]]; then
    msg_error "Expected marker count ${expected}, got ${actual}."
    exit 1
  fi
}

backup_linkvault() {
  local archive
  msg_info "Creating LinkVault backup"
  archive="$(ct_exec /tmp/backup-linkvault.sh | tail -n 1)"
  if [[ -z "${archive}" ]]; then
    msg_error "Backup script did not print an archive path."
    exit 1
  fi
  msg_ok "Backup created: ${archive}"
  printf "%s" "${archive}"
}

restore_linkvault() {
  local archive="$1"
  msg_info "Restoring LinkVault backup"
  if ct_exec /tmp/restore-linkvault.sh "${archive}" >>"${LOG_FILE}" 2>&1; then
    msg_ok "Restoring LinkVault backup"
    return
  fi

  msg_info "Restore command returned non-zero; checking whether service recovered"
  if wait_for_health; then
    msg_ok "LinkVault recovered after restore"
    return
  fi

  msg_error "Restoring LinkVault backup"
  echo "Last log lines from ${LOG_FILE}:" >&2
  tail -n 120 "${LOG_FILE}" >&2 || true
  exit 1
}

verify_health() {
  run_quiet "Checking LinkVault health" ct_exec curl -fsS "${HEALTH_URL}"
}

wait_for_health() {
  for _ in {1..60}; do
    if ct_exec curl -fsS "${HEALTH_URL}" >>"${LOG_FILE}" 2>&1; then
      return 0
    fi
    sleep 1
  done
  ct_exec systemctl status linkvault --no-pager >>"${LOG_FILE}" 2>&1 || true
  ct_exec journalctl -u linkvault -n 100 --no-pager >>"${LOG_FILE}" 2>&1 || true
  return 1
}

main() {
  : >"${LOG_FILE}"
  require_host

  echo "${APP} Proxmox LXC backup/restore smoke test"
  echo "CTID: ${CTID}"
  echo "Marker: ${MARKER_ID}"

  verify_health
  download_scripts
  insert_marker
  assert_marker_count 1

  local archive
  archive="$(backup_linkvault)"
  delete_marker
  assert_marker_count 0
  restore_linkvault "${archive}"
  assert_marker_count 1
  verify_health

  echo
  msg_ok "Backup/restore smoke test completed"
  echo "Container: ${CTID}"
  echo "Backup: ${archive}"
  echo "Marker restored: ${MARKER_ID}"
  echo "Log: ${LOG_FILE}"
}

main "$@"

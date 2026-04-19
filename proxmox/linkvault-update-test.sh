#!/usr/bin/env bash
set -Eeuo pipefail

# Run on the Proxmox VE host against an existing LinkVault LXC.
# Usage: LINKVAULT_CTID=112 ./proxmox/linkvault-update-test.sh

APP="LinkVault"
CTID="${LINKVAULT_CTID:-${1:-}}"
SCRIPT_BASE_URL="${LINKVAULT_SCRIPT_BASE_URL:-https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main}"
SCRIPT_CACHE_BUST="${LINKVAULT_SCRIPT_CACHE_BUST:-$(date -u +%s)}"
UPDATE_SCRIPT_URL="${SCRIPT_BASE_URL}/scripts/update-linkvault.sh?cb=${SCRIPT_CACHE_BUST}"
SOURCE_URL="${LINKVAULT_SOURCE_URL:-https://github.com/Nanja-at-web/LinkVault.git}"
SOURCE_REF="${LINKVAULT_SOURCE_REF:-main}"
HEALTH_URL="${LINKVAULT_HEALTH_URL:-http://127.0.0.1:3080/healthz}"
MARKER_ID="update_test_$(date -u +%Y%m%d%H%M%S)_${RANDOM}"
MARKER_URL="https://update-test.invalid/${MARKER_ID}"
LOG_FILE="${LINKVAULT_UPDATE_TEST_LOG:-/tmp/linkvault-update-test.log}"

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
  tail -n 120 "${LOG_FILE}" >&2 || true
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

download_script() {
  run_quiet "Installing update script inside CT ${CTID}" ct_exec bash -lc "
    set -euo pipefail
    command -v curl >/dev/null 2>&1 || (apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y curl ca-certificates)
    curl -fsSL '${UPDATE_SCRIPT_URL}' -o /tmp/update-linkvault.sh
    chmod +x /tmp/update-linkvault.sh
  "
}

insert_marker() {
  run_quiet "Creating update marker bookmark" ct_exec env MARKER_ID="${MARKER_ID}" MARKER_URL="${MARKER_URL}" /opt/linkvault/.venv/bin/python - <<'PY'
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
        "title": "LinkVault Update Marker",
        "description": "Temporary marker used by the Proxmox LXC update smoke test.",
        "tags": "update-test",
        "collections": "System",
        "favorite": True,
        "pinned": True,
        "notes": "This bookmark must survive update.",
    },
    enrich_metadata=False,
)
with store.connect() as connection:
    connection.execute("UPDATE bookmarks SET id = ? WHERE id = ?", (marker_id, bookmark.id))
    connection.execute("UPDATE bookmarks_fts SET bookmark_id = ? WHERE bookmark_id = ?", (marker_id, bookmark.id))
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

verify_health() {
  run_quiet "Checking LinkVault health" ct_exec curl -fsS "${HEALTH_URL}"
}

run_update() {
  run_quiet "Running LinkVault update" ct_exec env \
    LINKVAULT_SOURCE_URL="${SOURCE_URL}" \
    LINKVAULT_SOURCE_REF="${SOURCE_REF}" \
    LINKVAULT_HEALTH_URL="${HEALTH_URL}" \
    /tmp/update-linkvault.sh
}

main() {
  : >"${LOG_FILE}"
  require_host

  echo "${APP} Proxmox LXC update smoke test"
  echo "CTID: ${CTID}"
  echo "Source: ${SOURCE_URL} (${SOURCE_REF})"
  echo "Marker: ${MARKER_ID}"

  verify_health
  download_script
  insert_marker
  assert_marker_count 1
  run_update
  assert_marker_count 1
  verify_health

  echo
  msg_ok "Update smoke test completed"
  echo "Container: ${CTID}"
  echo "Marker survived: ${MARKER_ID}"
  echo "Log: ${LOG_FILE}"
}

main "$@"

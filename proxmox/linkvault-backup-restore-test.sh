#!/usr/bin/env bash
set -Eeuo pipefail

# Run on the Proxmox VE host against an existing LinkVault LXC.
# Usage: LINKVAULT_CTID=112 ./proxmox/linkvault-backup-restore-test.sh

APP="LinkVault"
CTID="${LINKVAULT_CTID:-${1:-}}"
SCRIPT_BASE_URL="${LINKVAULT_SCRIPT_BASE_URL:-https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main}"
BACKUP_SCRIPT_URL="${SCRIPT_BASE_URL}/scripts/backup-linkvault.sh"
RESTORE_SCRIPT_URL="${SCRIPT_BASE_URL}/scripts/restore-linkvault.sh"
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
  run_quiet "Creating restore marker bookmark" ct_exec env MARKER_ID="${MARKER_ID}" MARKER_URL="${MARKER_URL}" python3 - <<'PY'
from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

env_path = Path("/etc/linkvault/linkvault.env")
env: dict[str, str] = {}
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip("'\"")

data_path = env.get("LINKVAULT_DATA", "").strip()
data_file = Path(data_path) if data_path else Path(env.get("LINKVAULT_DATA_DIR", "/var/lib/linkvault")) / "linkvault.sqlite3"

marker_id = os.environ["MARKER_ID"]
marker_url = os.environ["MARKER_URL"]
now = datetime.now(UTC).isoformat()
domain = (urlsplit(marker_url).hostname or "").lower()

connection = sqlite3.connect(data_file)
with connection:
    connection.execute(
        """
        INSERT OR REPLACE INTO bookmarks (
            id, url, normalized_url, title, description, domain, favicon_url,
            tags, collections, favorite, pinned, notes, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            marker_id,
            marker_url,
            marker_url,
            "LinkVault Backup Restore Marker",
            "Temporary marker used by the Proxmox LXC restore smoke test.",
            domain,
            "",
            "backup-restore-test",
            "System",
            1,
            1,
            "This bookmark must survive restore.",
            now,
            now,
        ),
    )
    connection.execute("DELETE FROM bookmarks_fts WHERE bookmark_id = ?", (marker_id,))
    connection.execute(
        """
        INSERT INTO bookmarks_fts (bookmark_id, title, url, description, domain, tags, collections, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            marker_id,
            "LinkVault Backup Restore Marker",
            marker_url,
            "Temporary marker used by the Proxmox LXC restore smoke test.",
            domain,
            "backup-restore-test",
            "System",
            "This bookmark must survive restore.",
        ),
    )
connection.close()
PY
}

delete_marker() {
  run_quiet "Deleting marker after backup" ct_exec env MARKER_ID="${MARKER_ID}" python3 - <<'PY'
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

env_path = Path("/etc/linkvault/linkvault.env")
env: dict[str, str] = {}
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip("'\"")

data_path = env.get("LINKVAULT_DATA", "").strip()
data_file = Path(data_path) if data_path else Path(env.get("LINKVAULT_DATA_DIR", "/var/lib/linkvault")) / "linkvault.sqlite3"

connection = sqlite3.connect(data_file)
with connection:
    connection.execute("DELETE FROM bookmarks_fts WHERE bookmark_id = ?", (os.environ["MARKER_ID"],))
    connection.execute("DELETE FROM bookmarks WHERE id = ?", (os.environ["MARKER_ID"],))
connection.close()
PY
}

marker_count() {
  ct_exec env MARKER_ID="${MARKER_ID}" python3 - <<'PY'
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

env_path = Path("/etc/linkvault/linkvault.env")
env: dict[str, str] = {}
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip("'\"")

data_path = env.get("LINKVAULT_DATA", "").strip()
data_file = Path(data_path) if data_path else Path(env.get("LINKVAULT_DATA_DIR", "/var/lib/linkvault")) / "linkvault.sqlite3"

connection = sqlite3.connect(data_file)
count = connection.execute("SELECT COUNT(*) FROM bookmarks WHERE id = ?", (os.environ["MARKER_ID"],)).fetchone()[0]
connection.close()
print(count)
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
  run_quiet "Restoring LinkVault backup" ct_exec /tmp/restore-linkvault.sh "${archive}"
}

verify_health() {
  run_quiet "Checking LinkVault health" ct_exec curl -fsS "${HEALTH_URL}"
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

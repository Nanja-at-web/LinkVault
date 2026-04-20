#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${LINKVAULT_DATA_DIR:-/var/lib/linkvault}"
MIN_RAM_MB="${LINKVAULT_MIN_RAM_MB:-768}"
RECOMMENDED_RAM_MB="${LINKVAULT_RECOMMENDED_RAM_MB:-1024}"
MIN_DISK_MB="${LINKVAULT_MIN_DISK_MB:-1024}"
RECOMMENDED_DISK_MB="${LINKVAULT_RECOMMENDED_DISK_MB:-4096}"

FAILURES=0
WARNINGS=0

ok() {
  printf "  [OK] %s\n" "$1"
}

warn() {
  WARNINGS=$((WARNINGS + 1))
  printf "  [WARN] %s\n" "$1"
}

fail() {
  FAILURES=$((FAILURES + 1))
  printf "  [FAIL] %s\n" "$1"
}

header() {
  cat <<'EOF'
=================================================
 LinkVault Requirements Check
=================================================
EOF
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

check_os() {
  if [[ ! -r /etc/os-release ]]; then
    warn "Cannot read /etc/os-release."
    return
  fi

  # shellcheck disable=SC1091
  source /etc/os-release
  if [[ "${ID:-}" == "debian" ]]; then
    case "${VERSION_ID:-}" in
      12|13|13.*) ok "OS: Debian ${VERSION_ID}" ;;
      *) warn "OS: Debian ${VERSION_ID:-unknown}; Debian 13 is the current test target." ;;
    esac
    return
  fi

  warn "OS: ${PRETTY_NAME:-unknown}; Debian LXC is the supported install target."
}

check_systemd() {
  if command_exists systemctl && [[ -d /run/systemd/system ]]; then
    ok "systemd is available."
  else
    fail "systemd is required for the service installer."
  fi
}

check_memory() {
  if [[ ! -r /proc/meminfo ]]; then
    warn "Cannot read memory information."
    return
  fi

  local mem_kb mem_mb
  mem_kb="$(awk '/MemTotal:/ {print $2}' /proc/meminfo)"
  mem_mb=$((mem_kb / 1024))
  if (( mem_mb < MIN_RAM_MB )); then
    fail "RAM: ${mem_mb} MB available; minimum for current MVP is ${MIN_RAM_MB} MB."
  elif (( mem_mb < RECOMMENDED_RAM_MB )); then
    warn "RAM: ${mem_mb} MB available; recommended is ${RECOMMENDED_RAM_MB} MB or more."
  else
    ok "RAM: ${mem_mb} MB available."
  fi
}

existing_path_for_df() {
  local path="$1"
  while [[ ! -e "${path}" && "${path}" != "/" ]]; do
    path="$(dirname "${path}")"
  done
  printf "%s\n" "${path}"
}

check_disk() {
  local target available
  target="$(existing_path_for_df "${DATA_DIR}")"
  available="$(df -Pm "${target}" | awk 'NR == 2 {print $4}')"
  if [[ -z "${available}" ]]; then
    warn "Cannot determine free disk space for ${DATA_DIR}."
    return
  fi

  if (( available < MIN_DISK_MB )); then
    fail "Disk: ${available} MB free near ${DATA_DIR}; minimum is ${MIN_DISK_MB} MB."
  elif (( available < RECOMMENDED_DISK_MB )); then
    warn "Disk: ${available} MB free near ${DATA_DIR}; recommended is ${RECOMMENDED_DISK_MB} MB or more."
  else
    ok "Disk: ${available} MB free near ${DATA_DIR}."
  fi
}

check_command_set() {
  local missing=()
  for name in "$@"; do
    command_exists "${name}" || missing+=("${name}")
  done

  if (( ${#missing[@]} )); then
    fail "Missing commands: ${missing[*]}"
  else
    ok "Required commands present: $*"
  fi
}

check_ca_certificates() {
  if [[ -r /etc/ssl/certs/ca-certificates.crt || -d /etc/ssl/certs ]]; then
    ok "CA certificates are available."
  else
    fail "CA certificates are required for HTTPS downloads."
  fi
}

check_python() {
  if ! command_exists python3; then
    fail "python3 is required."
    return
  fi

  if python3 - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
  then
    ok "Python version is >= 3.10."
  else
    fail "Python 3.10 or newer is required."
  fi

  if python3 - <<'PY'
import sqlite3
connection = sqlite3.connect(":memory:")
connection.execute("CREATE VIRTUAL TABLE linkvault_fts_check USING fts5(value)")
PY
  then
    ok "SQLite FTS5 is available through Python."
  else
    fail "SQLite FTS5 support is required for full-text search."
  fi

  if python3 -m venv --help >/dev/null 2>&1; then
    ok "python3 venv support is available."
  else
    fail "python3-venv is required."
  fi
}

print_tiers() {
  cat <<EOF

Install profile:
  Core MVP: Python, SQLite, SQLite FTS5, systemd, curl, ca-certificates.
  Current LXC default: 2 vCPU, 1024 MB RAM, 16 GB disk.
  Later archive workers: more RAM/disk, browser tooling, image/PDF tooling.
  Later platform mode: PostgreSQL/search/worker split only when features need it.
EOF
}

main() {
  header
  check_os
  check_systemd
  check_memory
  check_disk
  check_command_set curl
  check_ca_certificates
  command_exists git && ok "git is available." || warn "git is not installed; update/install-from-source flows need it."
  check_python
  print_tiers

  echo
  if (( FAILURES > 0 )); then
    printf "Result: %s failure(s), %s warning(s).\n" "${FAILURES}" "${WARNINGS}"
    exit 1
  fi

  printf "Result: requirements passed with %s warning(s).\n" "${WARNINGS}"
}

main "$@"

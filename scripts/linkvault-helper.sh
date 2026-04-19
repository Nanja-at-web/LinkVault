#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${LINKVAULT_SERVICE_NAME:-linkvault}"
CONFIG_FILE="${LINKVAULT_CONFIG_FILE:-/etc/linkvault/linkvault.env}"
DATA_DIR="${LINKVAULT_DATA_DIR:-/var/lib/linkvault}"
BACKUP_DIR="${LINKVAULT_BACKUP_DIR:-/var/backups/linkvault}"
HEALTH_URL="${LINKVAULT_HEALTH_URL:-http://127.0.0.1:3080/healthz}"
BACKUP_CMD="${LINKVAULT_BACKUP_CMD:-/usr/local/bin/backup-linkvault.sh}"
RESTORE_CMD="${LINKVAULT_RESTORE_CMD:-/usr/local/bin/restore-linkvault.sh}"
UPDATE_CMD="${LINKVAULT_UPDATE_CMD:-/usr/local/bin/update-linkvault.sh}"

if [[ -f "${CONFIG_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "${CONFIG_FILE}"
  set +a
  DATA_DIR="${LINKVAULT_DATA_DIR:-${DATA_DIR}}"
fi

print_header() {
  cat <<'EOF'
=================================================
 LinkVault Helper
=================================================
EOF
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "Run this action as root." >&2
    exit 1
  fi
}

pause() {
  if [[ -t 0 ]]; then
    printf "\nPress Enter to continue..."
    read -r _ || true
  fi
}

show_overview() {
  print_header
  echo "Service: ${SERVICE_NAME}"
  echo "Config:  ${CONFIG_FILE}"
  echo "Data:    ${DATA_DIR}"
  echo "Backup:  ${BACKUP_DIR}"
  echo "Health:  ${HEALTH_URL}"
  echo
  systemctl is-active "${SERVICE_NAME}" >/dev/null 2>&1 \
    && echo "Status:  active" \
    || echo "Status:  not active"
}

show_status() {
  systemctl status "${SERVICE_NAME}" --no-pager
}

show_logs() {
  journalctl -u "${SERVICE_NAME}" -n "${LINKVAULT_LOG_LINES:-120}" --no-pager
}

healthcheck() {
  curl -fsS "${HEALTH_URL}"
  echo
}

show_token() {
  if [[ ! -f "${CONFIG_FILE}" ]]; then
    echo "Config file not found: ${CONFIG_FILE}" >&2
    exit 1
  fi
  local token
  token="$(sed -n 's/^LINKVAULT_SETUP_TOKEN=//p' "${CONFIG_FILE}" | tail -n 1)"
  if [[ -z "${token}" ]]; then
    echo "No LINKVAULT_SETUP_TOKEN found in ${CONFIG_FILE}."
    return
  fi
  echo "${token}"
}

run_backup() {
  require_root
  if [[ ! -x "${BACKUP_CMD}" ]]; then
    echo "Backup command not found or not executable: ${BACKUP_CMD}" >&2
    exit 1
  fi
  "${BACKUP_CMD}"
}

latest_backup() {
  find "${BACKUP_DIR}" -maxdepth 1 -type f -name 'linkvault-backup-*.tar.gz' 2>/dev/null \
    | sort \
    | tail -n 1
}

run_restore() {
  require_root
  if [[ ! -x "${RESTORE_CMD}" ]]; then
    echo "Restore command not found or not executable: ${RESTORE_CMD}" >&2
    exit 1
  fi

  local archive="${1:-}"
  if [[ -z "${archive}" ]]; then
    archive="$(latest_backup)"
    if [[ -z "${archive}" ]]; then
      echo "No backup archive found in ${BACKUP_DIR}." >&2
      exit 1
    fi
    if [[ -t 0 ]]; then
      read -r -p "Restore latest backup ${archive}? [y/N] " answer
      case "${answer}" in
        y|Y|yes|YES) ;;
        *) echo "Restore cancelled."; return ;;
      esac
    fi
  fi

  "${RESTORE_CMD}" "${archive}"
}

run_update() {
  require_root
  if [[ ! -x "${UPDATE_CMD}" ]]; then
    echo "Update command not found or not executable: ${UPDATE_CMD}" >&2
    exit 1
  fi
  "${UPDATE_CMD}"
}

print_usage() {
  cat <<EOF
Usage: linkvault-helper [command]

Commands:
  menu       Open the interactive menu.
  overview   Show paths and service state.
  status     Show systemd service status.
  logs       Show recent journal logs.
  health     Run the local healthcheck.
  backup     Create a LinkVault backup.
  restore    Restore a backup archive. Optional: linkvault-helper restore /path/archive.tar.gz
  update     Update LinkVault from the configured Git source.
  token      Print the initial setup token.
  help       Show this help.
EOF
}

menu() {
  while true; do
    clear 2>/dev/null || true
    show_overview
    cat <<'EOF'

1) Service status
2) Recent logs
3) Healthcheck
4) Create backup
5) Restore latest backup
6) Update LinkVault
7) Show setup token
8) Exit
EOF
    printf "\nChoose an option: "
    read -r choice || exit 0

    case "${choice}" in
      1) show_status; pause ;;
      2) show_logs; pause ;;
      3) healthcheck; pause ;;
      4) run_backup; pause ;;
      5) run_restore; pause ;;
      6) run_update; pause ;;
      7) show_token; pause ;;
      8|q|Q) exit 0 ;;
      *) echo "Unknown option: ${choice}"; pause ;;
    esac
  done
}

command="${1:-menu}"
case "${command}" in
  menu) menu ;;
  overview) show_overview ;;
  status) show_status ;;
  logs) show_logs ;;
  health) healthcheck ;;
  backup) run_backup ;;
  restore) shift || true; run_restore "${1:-}" ;;
  update) run_update ;;
  token) show_token ;;
  help|-h|--help) print_usage ;;
  *) echo "Unknown command: ${command}" >&2; print_usage >&2; exit 1 ;;
esac

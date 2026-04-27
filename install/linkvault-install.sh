#!/usr/bin/env bash
set -Eeuo pipefail

# Experimental container-side installer for LinkVault.
# This mirrors the community-scripts split between ct/*.sh and install/*.sh.

APP="LinkVault"
REPO_URL="${LINKVAULT_REPO_URL:-https://github.com/Nanja-at-web/LinkVault.git}"
BRANCH="${LINKVAULT_BRANCH:-main}"
WORKDIR="${LINKVAULT_WORKDIR:-/tmp/linkvault-install-test}"
HEALTH_URL="${LINKVAULT_HEALTH_URL:-http://127.0.0.1:3080/healthz}"
LOG_FILE="${LINKVAULT_INSTALL_LOG:-/tmp/linkvault-install.log}"

export LANG=C.UTF-8
export LC_ALL=C.UTF-8

if [[ -t 1 ]]; then
  CL="\033[m"
  GN="\033[1;92m"
  BL="\033[36m"
  YW="\033[33m"
  RD="\033[01;31m"
else
  CL=""
  GN=""
  BL=""
  YW=""
  RD=""
fi

msg_info() {
  printf "%b\n" "  ${BL}[*]${CL} $1"
}

msg_ok() {
  printf "%b\n" "  ${GN}[OK]${CL} $1"
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
  tail -n 80 "${LOG_FILE}" >&2 || true
  exit 1
}

wait_for_linkvault() {
  msg_info "Waiting for LinkVault healthcheck"
  for _ in {1..60}; do
    if curl -fsS "${HEALTH_URL}" >>"${LOG_FILE}" 2>&1; then
      msg_ok "LinkVault healthcheck"
      return
    fi
    sleep 1
  done

  systemctl status linkvault --no-pager >>"${LOG_FILE}" 2>&1 || true
  journalctl -u linkvault -n 100 --no-pager >>"${LOG_FILE}" 2>&1 || true
  msg_error "LinkVault healthcheck"
  echo "Last log lines from ${LOG_FILE}:" >&2
  tail -n 120 "${LOG_FILE}" >&2 || true
  exit 1
}

main() {
  if [[ "${EUID}" -ne 0 ]]; then
    msg_error "Run this installer as root inside a Debian LXC."
    exit 1
  fi

  : >"${LOG_FILE}"
  msg_info "Installing ${APP}"

  run_quiet "Installing Dependencies" bash -lc \
    "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y git curl ca-certificates python3 python3-venv"

  rm -rf "${WORKDIR}"
  run_quiet "Cloning LinkVault" git clone --branch "${BRANCH}" --depth 1 "${REPO_URL}" "${WORKDIR}"
  run_quiet "Checking Requirements" "${WORKDIR}/scripts/check-requirements.sh"
  run_quiet "Installing LinkVault Service" "${WORKDIR}/scripts/install-debian.sh"
  wait_for_linkvault

  local ip token
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  token="$(sed -n 's/^LINKVAULT_SETUP_TOKEN=//p' /etc/linkvault/linkvault.env 2>/dev/null | tail -n 1 || true)"
  local port="${LINKVAULT_PORT:-3080}"

  msg_ok "Completed Successfully"
  printf "\n%b\n" "${GN}==================================================${CL}"
  printf "%b\n"   "${GN} ${APP} is ready!${CL}"
  printf "%b\n"   "${GN}==================================================${CL}"
  if [[ -n "${ip}" ]]; then
    printf "  %-18s %b\n" "URL:" "${GN}http://${ip}:${port}${CL}"
  else
    printf "  %-18s %b\n" "URL:" "${GN}http://<container-ip>:${port}${CL}"
  fi
  if [[ -n "${token}" ]]; then
    printf "  %-18s %b\n" "Setup token:" "${YW}${token}${CL}"
  fi
  printf "  %-18s %s\n" "Healthcheck:" "curl http://127.0.0.1:${port}/healthz"
  printf "  %-18s %s\n" "Logs:" "journalctl -u linkvault -f"
  printf "  %-18s %s\n" "Helper:" "linkvault-helper"
  printf "  %-18s %s\n" "Backup:" "linkvault-helper backup"
  printf "  %-18s %s\n" "Restore:" "linkvault-helper restore"
  printf "  %-18s %s\n" "Update:" "linkvault-helper update"
  printf "%b\n"   "${GN}==================================================${CL}"
}

main "$@"

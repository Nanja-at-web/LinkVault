#!/usr/bin/env bash
set -Eeuo pipefail

# Experimental Proxmox host installer for LinkVault.
# Run on the Proxmox VE host shell, not inside an existing container.

APP="LinkVault"
CTID="${LINKVAULT_CTID:-}"
HOSTNAME="${LINKVAULT_HOSTNAME:-linkvault}"
TEMPLATE_STORAGE="${LINKVAULT_TEMPLATE_STORAGE:-local}"
ROOTFS_STORAGE="${LINKVAULT_ROOTFS_STORAGE:-local-lvm}"
BRIDGE="${LINKVAULT_BRIDGE:-vmbr0}"
CORES="${LINKVAULT_CORES:-2}"
MEMORY="${LINKVAULT_MEMORY:-1024}"
DISK="${LINKVAULT_DISK:-16}"
REPO_URL="${LINKVAULT_REPO_URL:-https://github.com/Nanja-at-web/LinkVault.git}"
BRANCH="${LINKVAULT_BRANCH:-main}"
INSTALL_URL="${LINKVAULT_INSTALL_URL:-https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/install/linkvault-install.sh}"
LOG_FILE="${LINKVAULT_HOST_LOG:-/tmp/linkvault-ct-install.log}"

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

header_info() {
  clear 2>/dev/null || true
  printf "%b\n" "${BL}=================================================${CL}"
  printf "%b\n" "${GN} ${APP} LXC Installer${CL}"
  printf "%b\n" "${BL}=================================================${CL}"
}

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

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    msg_error "Run this script as root in the Proxmox VE shell."
    exit 1
  fi
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    msg_error "Required command not found: $1"
    echo "This script must run on a Proxmox VE host." >&2
    exit 1
  fi
}

next_ctid() {
  if [[ -n "${CTID}" ]]; then
    echo "${CTID}"
    return
  fi
  pvesh get /cluster/nextid
}

select_template() {
  run_quiet "Refreshing LXC Template List" pveam update

  local template
  template="$(pveam available --section system | awk '$2 ~ /^debian-13-standard_.*amd64\.tar\.(zst|gz)$/ {print $2; exit}')"
  if [[ -z "${template}" ]]; then
    template="$(pveam available --section system | awk '$2 ~ /^debian-12-standard_.*amd64\.tar\.(zst|gz)$/ {print $2; exit}')"
  fi
  if [[ -z "${template}" ]]; then
    msg_error "No Debian 13 or Debian 12 amd64 LXC template found via pveam."
    exit 1
  fi
  echo "${template}"
}

download_template_if_needed() {
  local template="$1"
  if pveam list "${TEMPLATE_STORAGE}" | awk -v storage="${TEMPLATE_STORAGE}" -v template="${template}" '
    $1 == template || $1 == storage ":vztmpl/" template { found = 1 }
    END { exit !found }
  '; then
    msg_ok "Using cached Template"
    return
  fi

  run_quiet "Downloading Template" pveam download "${TEMPLATE_STORAGE}" "${template}"
}

wait_for_container_network() {
  local ctid="$1"
  msg_info "Waiting for Network"
  for _ in {1..60}; do
    if pct exec "${ctid}" -- bash -lc "getent hosts github.com >/dev/null 2>&1" >>"${LOG_FILE}" 2>&1; then
      msg_ok "Network Connected"
      return
    fi
    sleep 2
  done

  msg_error "Network not ready inside CT ${ctid}"
  exit 1
}

install_bootstrap_packages() {
  local ctid="$1"
  run_quiet "Installing Bootstrap Packages" pct exec "${ctid}" -- bash -lc \
    "export LANG=C.UTF-8 LC_ALL=C.UTF-8 \
      && apt-get update \
      && DEBIAN_FRONTEND=noninteractive apt-get install -y curl ca-certificates"
}

install_linkvault() {
  local ctid="$1"
  run_quiet "Installing LinkVault" pct exec "${ctid}" -- bash -lc \
    "curl -fsSL '${INSTALL_URL}' -o /tmp/linkvault-install.sh \
      && chmod +x /tmp/linkvault-install.sh \
      && LINKVAULT_REPO_URL='${REPO_URL}' LINKVAULT_BRANCH='${BRANCH}' /tmp/linkvault-install.sh"
}

verify_linkvault() {
  local ctid="$1"
  msg_info "Checking Health"
  for _ in {1..60}; do
    if pct exec "${ctid}" -- curl -fsS http://127.0.0.1:3080/healthz >>"${LOG_FILE}" 2>&1; then
      msg_ok "Healthcheck Passed"
      return
    fi
    sleep 1
  done

  pct exec "${ctid}" -- systemctl status linkvault --no-pager >>"${LOG_FILE}" 2>&1 || true
  pct exec "${ctid}" -- journalctl -u linkvault -n 100 --no-pager >>"${LOG_FILE}" 2>&1 || true
  msg_error "LinkVault did not become healthy inside CT ${ctid}."
  echo "Last log lines from ${LOG_FILE}:" >&2
  tail -n 120 "${LOG_FILE}" >&2 || true
  exit 1
}

container_ip() {
  local ctid="$1"
  pct exec "${ctid}" -- bash -lc "hostname -I | awk '{print \$1}'" 2>/dev/null || true
}

setup_token() {
  local ctid="$1"
  pct exec "${ctid}" -- bash -lc "sed -n 's/^LINKVAULT_SETUP_TOKEN=//p' /etc/linkvault/linkvault.env | tail -n 1" 2>/dev/null || true
}

main() {
  : >"${LOG_FILE}"
  header_info
  require_root
  require_command pct
  require_command pveam
  require_command pvesh

  local ctid template ip token
  ctid="$(next_ctid)"
  template="$(select_template)"

  if pct status "${ctid}" >/dev/null 2>&1; then
    msg_error "CT ${ctid} already exists. Choose another ID with LINKVAULT_CTID=123."
    exit 1
  fi

  msg_info "Using CTID ${ctid}"
  msg_info "Using ${template}"
  msg_info "Using ${ROOTFS_STORAGE}:${DISK}G, ${CORES} CPU, ${MEMORY} MB RAM"

  download_template_if_needed "${template}"

  run_quiet "Creating LXC Container" pct create "${ctid}" "${TEMPLATE_STORAGE}:vztmpl/${template}" \
    --hostname "${HOSTNAME}" \
    --cores "${CORES}" \
    --memory "${MEMORY}" \
    --rootfs "${ROOTFS_STORAGE}:${DISK}" \
    --net0 "name=eth0,bridge=${BRIDGE},ip=dhcp" \
    --ostype debian \
    --unprivileged 1 \
    --features nesting=1 \
    --onboot 1

  run_quiet "Starting LXC Container" pct start "${ctid}"
  wait_for_container_network "${ctid}"
  install_bootstrap_packages "${ctid}"
  install_linkvault "${ctid}"
  verify_linkvault "${ctid}"

  ip="$(container_ip "${ctid}")"
  token="$(setup_token "${ctid}")"

  echo
  msg_ok "Completed Successfully"
  printf "%b\n" "  ${YW}Access it using:${CL}"
  if [[ -n "${ip}" ]]; then
    printf "%b\n" "  ${GN}http://${ip}:3080${CL}"
  else
    printf "%b\n" "  ${GN}Open the container IP on port 3080.${CL}"
  fi
  if [[ -n "${token}" ]]; then
    printf "%b\n" "  Setup token: ${GN}${token}${CL}"
  fi
  printf "%b\n" "  Healthcheck: pct exec ${ctid} -- curl -fsS http://127.0.0.1:3080/healthz"
  printf "%b\n" "  Log: ${LOG_FILE}"
}

main "$@"

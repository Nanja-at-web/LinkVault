#!/usr/bin/env bash
set -euo pipefail

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
INSTALL_URL="${LINKVAULT_INSTALL_URL:-https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-lxc-test.sh}"

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "Run this script as root in the Proxmox VE shell." >&2
    exit 1
  fi
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
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
  pveam update >/dev/null
  local template
  template="$(pveam available --section system | awk '$2 ~ /^debian-13-standard_.*amd64\.tar\.(zst|gz)$/ {print $2; exit}')"
  if [[ -z "${template}" ]]; then
    template="$(pveam available --section system | awk '$2 ~ /^debian-12-standard_.*amd64\.tar\.(zst|gz)$/ {print $2; exit}')"
  fi
  if [[ -z "${template}" ]]; then
    echo "No Debian 13 or Debian 12 amd64 LXC template found via pveam." >&2
    exit 1
  fi
  echo "${template}"
}

download_template_if_needed() {
  local template="$1"
  if ! pveam list "${TEMPLATE_STORAGE}" | awk -v storage="${TEMPLATE_STORAGE}" -v template="${template}" '
    $1 == template || $1 == storage ":vztmpl/" template { found = 1 }
    END { exit !found }
  '; then
    pveam download "${TEMPLATE_STORAGE}" "${template}"
  fi
}

wait_for_container_network() {
  local ctid="$1"
  echo "Waiting for network inside CT ${ctid}..."
  for _ in {1..60}; do
    if pct exec "${ctid}" -- bash -lc "getent hosts github.com >/dev/null 2>&1"; then
      return
    fi
    sleep 2
  done
  echo "Timed out waiting for network/DNS inside CT ${ctid}." >&2
  exit 1
}

container_ip() {
  local ctid="$1"
  pct exec "${ctid}" -- bash -lc "hostname -I | awk '{print \$1}'" 2>/dev/null || true
}

main() {
  require_root
  require_command pct
  require_command pveam
  require_command pvesh

  local ctid template ip
  ctid="$(next_ctid)"
  template="$(select_template)"

  if pct status "${ctid}" >/dev/null 2>&1; then
    echo "CT ${ctid} already exists. Choose another ID with LINKVAULT_CTID=123." >&2
    exit 1
  fi

  echo "Installing ${APP} in new Debian LXC"
  echo "CTID: ${ctid}"
  echo "Hostname: ${HOSTNAME}"
  echo "Template: ${template}"
  echo "Rootfs: ${ROOTFS_STORAGE}:${DISK}G"

  download_template_if_needed "${template}"

  pct create "${ctid}" "${TEMPLATE_STORAGE}:vztmpl/${template}" \
    --hostname "${HOSTNAME}" \
    --cores "${CORES}" \
    --memory "${MEMORY}" \
    --rootfs "${ROOTFS_STORAGE}:${DISK}" \
    --net0 "name=eth0,bridge=${BRIDGE},ip=dhcp" \
    --ostype debian \
    --unprivileged 1 \
    --features nesting=1 \
    --onboot 1

  pct start "${ctid}"
  wait_for_container_network "${ctid}"

  pct exec "${ctid}" -- bash -lc \
    "LINKVAULT_REPO_URL='${REPO_URL}' LINKVAULT_BRANCH='${BRANCH}' bash -c \"\$(curl -fsSL '${INSTALL_URL}')\""

  ip="$(container_ip "${ctid}")"
  echo
  echo "${APP} installation completed."
  echo "Container: ${ctid}"
  if [[ -n "${ip}" ]]; then
    echo "Open: http://${ip}:3080"
  else
    echo "Open the container IP on port 3080."
  fi
  echo "Healthcheck: pct exec ${ctid} -- curl -fsS http://127.0.0.1:3080/healthz"
}

main "$@"

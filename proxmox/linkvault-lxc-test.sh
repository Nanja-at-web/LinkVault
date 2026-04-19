#!/usr/bin/env bash
set -euo pipefail

# Internal smoke-test helper for a Debian LXC. This is not a community-scripts
# submission yet; it proves that the Debian installer works inside a container.

REPO_URL="${LINKVAULT_REPO_URL:-https://github.com/Nanja-at-web/LinkVault.git}"
BRANCH="${LINKVAULT_BRANCH:-main}"
WORKDIR="${LINKVAULT_WORKDIR:-/tmp/linkvault-install-test}"
HEALTH_URL="${LINKVAULT_HEALTH_URL:-http://127.0.0.1:3080/healthz}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script as root inside a Debian LXC." >&2
  exit 1
fi

apt-get update
apt-get install -y git curl ca-certificates

rm -rf "${WORKDIR}"
git clone --branch "${BRANCH}" --depth 1 "${REPO_URL}" "${WORKDIR}"

"${WORKDIR}/scripts/install-debian.sh"

wait_for_linkvault() {
  echo "Waiting for LinkVault healthcheck..."
  for _ in {1..60}; do
    if curl -fsS "${HEALTH_URL}"; then
      echo
      return
    fi
    sleep 1
  done

  systemctl status linkvault --no-pager || true
  journalctl -u linkvault -n 100 --no-pager || true
  echo "LinkVault did not become healthy at ${HEALTH_URL}" >&2
  exit 1
}

wait_for_linkvault
systemctl status linkvault --no-pager
echo
echo "LinkVault LXC smoke test completed."

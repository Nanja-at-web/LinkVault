#!/usr/bin/env bash
set -euo pipefail

# Internal smoke-test helper for a Debian LXC. This is not a community-scripts
# submission yet; it proves that the Debian installer works inside a container.

REPO_URL="${LINKVAULT_REPO_URL:-https://github.com/Nanja-at-web/LinkVault.git}"
BRANCH="${LINKVAULT_BRANCH:-main}"
WORKDIR="${LINKVAULT_WORKDIR:-/tmp/linkvault-install-test}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script as root inside a Debian LXC." >&2
  exit 1
fi

apt-get update
apt-get install -y git curl ca-certificates

rm -rf "${WORKDIR}"
git clone --branch "${BRANCH}" --depth 1 "${REPO_URL}" "${WORKDIR}"

"${WORKDIR}/scripts/install-debian.sh"

systemctl status linkvault --no-pager
curl -fsS http://127.0.0.1:3080/healthz
echo
echo "LinkVault LXC smoke test completed."

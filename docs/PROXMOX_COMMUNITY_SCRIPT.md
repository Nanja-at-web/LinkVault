# Proxmox Community-Scripts Zielbild

## Ziel

LinkVault soll ueber community-scripts.org als LXC installierbar werden. Die
Community-Scripts-Dokumentation beschreibt dafuer zwei Teile:

- `ct/linkvault.sh`: Einstiegspunkt auf dem Proxmox-Host.
- `install/linkvault-install.sh`: Installation innerhalb des LXC-Containers.

## Vorgeschlagene Defaults

| Einstellung | Wert |
|---|---|
| Container | unprivileged LXC |
| OS | Debian 13 |
| CPU | 2 vCPU |
| RAM | 4096 MB |
| Disk | 16 GB |
| Port | 3080 |
| Datenbank | PostgreSQL lokal |
| Reverse Proxy | optional, nicht erzwungen |

Begruendung: LinkVault soll leichter als Linkwarden/Karakeep bleiben, braucht
aber fuer Archivierung, Screenshot/PDF und Suche mehr Reserve als ein reiner
Minimal-Bookmark-Manager.

## `ct/linkvault.sh` Skizze

```bash
#!/usr/bin/env bash

# Copyright (c) 2026 community-scripts ORG
# Author: LinkVault contributors
# License: MIT
# Source: https://github.com/linkvault/linkvault

source <(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/misc/build.func)

APP="LinkVault"
var_tags="bookmarks;archive;knowledge"
var_cpu="2"
var_ram="4096"
var_disk="16"
var_os="debian"
var_version="13"
var_unprivileged="1"

header_info "$APP"
variables
color
catch_errors

function update_script() {
  header_info
  check_container_storage
  check_container_resources
  if [[ ! -d /opt/linkvault ]]; then
    msg_error "No ${APP} Installation Found!"
    exit
  fi
  msg_info "Updating ${APP}"
  systemctl stop linkvault
  # download latest release, run migrations, restart service
  systemctl start linkvault
  msg_ok "Updated ${APP}"
}

start
build_container
description

msg_ok "Completed Successfully!"
echo -e "${INFO}${YW} Access it using:${CL}"
echo -e "${TAB}${GATEWAY}${BGN}http://${IP}:3080${CL}"
```

## `install/linkvault-install.sh` Aufgaben

```bash
#!/usr/bin/env bash

set -euo pipefail

# 1. Basispakete
# apt-get update
# apt-get install -y curl ca-certificates postgresql

# 2. Systemuser
# useradd --system --home /opt/linkvault --shell /usr/sbin/nologin linkvault

# 3. Verzeichnisse
# install -d -o linkvault -g linkvault /opt/linkvault /var/lib/linkvault /var/log/linkvault

# 4. Release laden
# curl -fsSL "$RELEASE_URL" -o /tmp/linkvault.tar.gz
# tar -xzf /tmp/linkvault.tar.gz -C /opt/linkvault --strip-components=1

# 5. Datenbank anlegen
# sudo -u postgres createuser linkvault
# sudo -u postgres createdb -O linkvault linkvault

# 6. Konfiguration schreiben
# /etc/linkvault/linkvault.env

# 7. Migrationen
# /opt/linkvault/linkvault migrate

# 8. systemd Service
# systemctl enable --now linkvault
```

## Konfigurationsdatei

```env
LINKVAULT_ADDR=0.0.0.0:3080
LINKVAULT_DATABASE_URL=postgres://linkvault@localhost/linkvault
LINKVAULT_DATA_DIR=/var/lib/linkvault
LINKVAULT_PUBLIC_URL=http://localhost:3080
LINKVAULT_AI_ENABLED=false
LINKVAULT_ARCHIVE_SCREENSHOTS=true
LINKVAULT_ARCHIVE_PDF=true
```

## Community-Scripts Einreichung

Vor einer Einreichung braucht das Projekt:

- oeffentliches Release-Artefakt fuer Linux amd64/arm64
- dokumentierte Port- und Datenpfade
- Update-Befehl oder Update-Funktion
- Healthcheck-Endpunkt, z. B. `/healthz`
- systemd Unit
- Backup-Hinweise fuer DB und `/var/lib/linkvault`
- klare Lizenz

## Hinweise aus aktueller Pruefung

Am 18.04.2026 nennt das Community-Scripts-Repository als Anforderungen
Proxmox VE 8.4, 9.0 oder 9.1, Root-Shell-Zugriff und Netzwerkzugang. Die
Dokumentation beschreibt `ct/*.sh` als Host-seitige Container-Skripte und
`install/*.sh` als containerseitige Installationsskripte.

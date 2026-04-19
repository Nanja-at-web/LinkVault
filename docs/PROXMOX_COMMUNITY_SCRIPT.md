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
| RAM | 1024 MB fuer aktuellen Python-MVP, spaeter 4096 MB mit Archivierung |
| Disk | 16 GB |
| Port | 3080 |
| Datenbank | SQLite unter `/var/lib/linkvault`, PostgreSQL spaeter |
| Erstes Setup | initialer Admin via `LINKVAULT_SETUP_TOKEN` |
| Reverse Proxy | optional, nicht erzwungen |

Begruendung: Der aktuelle Python-MVP soll leicht in einem Debian-LXC laufen.
Fuer spaetere Archivierung, Screenshot/PDF und groessere Volltextsuche wird
mehr RAM sinnvoll.

## Aktueller Vorbereitungsstand

Vor dem offiziellen community-scripts.org-Layout gibt es im Repo jetzt die
noetige Dienst-Vorarbeit:

- `deploy/linkvault.service`: systemd Unit fuer den Dienstbetrieb.
- `deploy/linkvault.env.example`: Service-Konfiguration fuer Port und Datenpfad.
- `scripts/install-debian.sh`: lokaler Debian-Installer fuer den Python-MVP.
- `scripts/backup-linkvault.sh`: konsistentes SQLite-Backup im laufenden Betrieb.
- `scripts/restore-linkvault.sh`: Restore mit Dienststopp und Vorher-Kopie.
- `ct/linkvault.sh`: community-scripts-aehnlicher Proxmox-Host-Einzeiler fuer neuen Debian-LXC.
- `install/linkvault-install.sh`: community-scripts-aehnlicher Installer innerhalb des Containers.
- `proxmox/linkvault-lxc-test.sh`: interner Smoke-Test in einem Debian-LXC.
- `docs/DEBIAN_LXC_TEST.md`: reproduzierbare Testprozedur fuer frische LXC.
- `docs/BACKUP_RESTORE.md`: Backup/Restore-Ablauf fuer den SQLite-MVP.

Das ist bewusst noch keine finale Einreichung. Der naechste Nachweis ist, dass
der Debian-Installer wiederholbar in einem frischen LXC startet und
`/healthz` erreichbar ist.

## Proxmox-Host-Einzeiler

Experimenteller Installationsweg in der Proxmox VE Shell:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/ct/linkvault.sh)"
```

Der Einzeiler erstellt einen neuen Debian-LXC, startet ihn und fuehrt im
Container den LinkVault-Installer aus. Er ist noch kein offizielles
community-scripts.org-Skript, aber entspricht dem gewuenschten Testablauf fuer
einen ersten Proxmox-Host-Install.

Der Host-Installer installiert im frischen Container zuerst `curl` und
`ca-certificates`, laedt danach den LinkVault-LXC-Smoke-Test nach `/tmp` und
prueft am Ende den Healthcheck.

Die Ausgabe ist inzwischen bewusst community-scripts-aehnlich: kurzer Header,
`[OK]`-Statuszeilen, lange `apt`, `pct` und `pip`-Ausgaben in
`/tmp/linkvault-ct-install.log`, danach URL und Healthcheck-Befehl.

Optionale Overrides:

```bash
LINKVAULT_CTID=140 \
LINKVAULT_ROOTFS_STORAGE=local-lvm \
LINKVAULT_TEMPLATE_STORAGE=local \
LINKVAULT_BRIDGE=vmbr0 \
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/ct/linkvault.sh)"
```

## Stufenplan Richtung community-scripts

Die Community-Scripts-Dokumentation ist gross genug, dass LinkVault dieses
Thema schrittweise behandeln sollte. Der aktuelle Einzeiler im LinkVault-Repo
ist ein funktionierender Proxmox-Testpfad, aber noch nicht der offizielle
Community-Scripts-Beitrag.

1. **Repo-eigener Testinstaller**: `ct/linkvault.sh` erstellt einen Debian-LXC
   und installiert LinkVault. Diese Stufe ist fuer schnelle echte
   Proxmox-Tests gedacht.
2. **Betriebsreife nachweisen**: Backup, Restore, Update, Healthcheck,
   journald-Logs und Datenpfade muessen in frischen LXC reproduzierbar
   funktionieren.
3. **Community-Scripts-Konventionen uebernehmen**: Host-Skript und
   Container-Installer werden an `build.func`, `install.func`, Default-/Advanced
   Mode, konsistente Statusausgabe, Developer-Flags und einen Post-Install
   Helper angepasst.
4. **Neue Script-Einreichung in ProxmoxVED**: Neue Anwendungen werden laut
   Contribution-Hinweisen zuerst in `community-scripts/ProxmoxVED`
   eingereicht, nicht direkt in `community-scripts/ProxmoxVE`.
5. **Promotion und Pflege**: Nach erfolgreicher Vorpruefung kann die
   Integration in den Hauptbestand wandern. Spaetere Fixes an einem bereits
   existierenden LinkVault-Skript gehoeren dann in `ProxmoxVE`.
6. **ProxmoxVE-Local pruefen**: Wenn das offizielle Skriptformat steht, sollte
   LinkVault auch mit `community-scripts/ProxmoxVE-Local` getestet werden.

## Offizielles community-scripts-Zielbild

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
# apt-get install -y python3 python3-venv curl ca-certificates

# 2. Systemuser
# useradd --system --home /opt/linkvault --shell /usr/sbin/nologin linkvault

# 3. Verzeichnisse
# install -d -o linkvault -g linkvault /opt/linkvault /var/lib/linkvault

# 4. Release laden
# curl -fsSL "$RELEASE_URL" -o /tmp/linkvault.tar.gz
# tar -xzf /tmp/linkvault.tar.gz -C /opt/linkvault --strip-components=1

# 5. SQLite-Datenpfad vorbereiten
# /var/lib/linkvault/linkvault.sqlite3

# 6. Konfiguration schreiben
# /etc/linkvault/linkvault.env

# 7. Migrationen
# Aktuell laufen SQLite-Migrationen beim Dienststart.

# 8. systemd Service
# systemctl enable --now linkvault
```

Im Repo existiert bereits ein experimentelles `install/linkvault-install.sh`.
Fuer eine echte community-scripts.org-Einreichung muesste dieses Skript noch
auf deren `install.func` und Review-Konventionen umgestellt werden.

## Konfigurationsdatei

```env
LINKVAULT_ADDR=0.0.0.0:3080
LINKVAULT_DATA_DIR=/var/lib/linkvault
```

Die Datei `/etc/linkvault/linkvault.env` enthaelt auch
`LINKVAULT_SETUP_TOKEN`. Sie muss deshalb `root:linkvault` und `0640` sein:
nicht weltlesbar, aber fuer den Dienstuser `linkvault` lesbar.

## Community-Scripts Einreichung

Vor einer Einreichung braucht das Projekt:

- oeffentliches Release-Artefakt fuer Linux amd64/arm64
- dokumentierte Port- und Datenpfade
- Update-Befehl oder Update-Funktion
- Healthcheck-Endpunkt, z. B. `/healthz`
- systemd Unit
- Backup-Hinweise fuer DB und `/var/lib/linkvault`
- klare Lizenz

Neue Skripte sollten zuerst gegen `community-scripts/ProxmoxVED` vorbereitet
werden. Eine direkte neue-Script-PR gegen `community-scripts/ProxmoxVE` waere
nach den aktuellen Contribution-Hinweisen der falsche Weg und wuerde
voraussichtlich geschlossen.

Relevante Quellen fuer die spaetere Umsetzung:

- `https://github.com/community-scripts/ProxmoxVE`
- `https://github.com/community-scripts/ProxmoxVED`
- `https://community-scripts.github.io/ProxmoxVED/`
- `https://community-scripts.org/docs/ct/readme`
- `https://community-scripts.org/docs/install/readme`
- `https://community-scripts.org/docs/misc/readme`
- `https://community-scripts.org/docs/vm/readme`
- `https://github.com/community-scripts/ProxmoxVE-Local`

## Aktueller Teststatus

Am 19.04.2026 wurde der experimentelle Proxmox-Host-Einzeiler erfolgreich auf
einem echten Proxmox-Host getestet:

```text
Host: proxbox
Kernel: Linux 6.17.13-2-pve x86_64
Container-ID: 112
Template: debian-13-standard_13.1-2_amd64.tar.zst
Rootfs: local-lvm:16G
Healthcheck: erfolgreich
URL: http://192.168.1.132:3080
```

Am 19.04.2026 wurde zusaetzlich der Backup/Restore-Smoke-Test im echten
Proxmox-LXC erfolgreich ausgefuehrt:

```text
Container-ID: 112
Backup: /var/backups/linkvault/linkvault-backup-20260419-152335.tar.gz
Restore-Marker: backup_restore_20260419152330_13602
Healthcheck vor Restore: erfolgreich
Healthcheck nach Restore: erfolgreich
Service nach Restore: active (running)
```

Ein Update-Test, ein Post-Install Helper und die Umstellung auf die offiziellen
Community-Scripts-Helfer bleiben vor einer ProxmoxVED-Einreichung offen.

## Hinweise aus aktueller Pruefung

Am 18.04.2026 nennt das Community-Scripts-Repository als Anforderungen
Proxmox VE 8.4, 9.0 oder 9.1, Root-Shell-Zugriff und Netzwerkzugang. Die
Dokumentation beschreibt `ct/*.sh` als Host-seitige Container-Skripte und
`install/*.sh` als containerseitige Installationsskripte.

Am 19.04.2026 wurde zusaetzlich festgehalten: Neue Skripte sollen zuerst in
`community-scripts/ProxmoxVED` getestet und eingereicht werden. Der Hauptrepo
`community-scripts/ProxmoxVE` ist fuer bestehende Skripte, Fixes und spaetere
Pflege relevant.

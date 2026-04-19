# Debian-LXC Installationstest

## Status

Der Proxmox-Host-Einzeiler wurde am 19.04.2026 erstmals erfolgreich auf einem
echten Proxmox-Host getestet.

```text
Host: proxbox
Kernel: Linux 6.17.13-2-pve x86_64
Container-ID: 112
Template: debian-13-standard_13.1-2_amd64.tar.zst
Rootfs: local-lvm:16G
IP: 192.168.1.17
Healthcheck: erfolgreich
URL: http://192.168.1.17:3080
```

Auf dem aktuellen Entwicklungsrechner wurde zusaetzlich geprueft:

```text
OS: Darwin/macOS
Proxmox pct: nicht vorhanden
LXC tools: nicht vorhanden
Docker: nicht vorhanden
```

Darum kann der frische LXC-Test lokal nicht direkt wiederholt werden. Die
folgenden Schritte bleiben die reproduzierbare Testprozedur fuer weitere
Proxmox-Laeufe.

## Frischer Debian-LXC

Empfohlene Testdaten:

```text
OS: Debian 13
CPU: 2 vCPU
RAM: 1024 MB
Disk: 16 GB
Netzwerk: Internetzugang fuer apt und GitHub
User: root im Container
```

## Proxmox-Host-Einzeiler

In der Proxmox VE Shell kann ein neuer Debian-LXC experimentell so erstellt
und installiert werden:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/ct/linkvault.sh)"
```

Der Befehl laeuft auf dem Proxmox-Host. Er erstellt den Container selbst,
startet ihn und fuehrt darin den LinkVault-Installer aus.

Die Ausgabe ist community-scripts-aehnlich gehalten: kurze Statuszeilen,
lange Installationsausgaben im Log und am Ende URL plus Healthcheck-Befehl.
Das Host-Log liegt standardmaessig hier:

```text
/tmp/linkvault-ct-install.log
```

Wenn ein frueher Testlauf mit `curl: command not found` im Container
abgebrochen ist, kann der bestehende Container manuell repariert werden:

```bash
pct exec 112 -- bash -lc 'apt-get update && apt-get install -y curl ca-certificates'
pct exec 112 -- bash -lc 'curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-lxc-test.sh -o /tmp/linkvault-lxc-test.sh && chmod +x /tmp/linkvault-lxc-test.sh && /tmp/linkvault-lxc-test.sh'
pct exec 112 -- curl -fsS http://127.0.0.1:3080/healthz
```

`112` dabei durch die eigene CTID ersetzen.

Optionale Variablen:

```bash
LINKVAULT_CTID=140
LINKVAULT_HOSTNAME=linkvault
LINKVAULT_ROOTFS_STORAGE=local-lvm
LINKVAULT_TEMPLATE_STORAGE=local
LINKVAULT_BRIDGE=vmbr0
LINKVAULT_CORES=2
LINKVAULT_MEMORY=1024
LINKVAULT_DISK=16
```

## Installationstest

Im Container:

```bash
apt-get update
apt-get install -y git curl ca-certificates
git clone --branch main --depth 1 https://github.com/Nanja-at-web/LinkVault.git /tmp/linkvault
/tmp/linkvault/scripts/install-debian.sh
```

Danach pruefen:

```bash
systemctl status linkvault --no-pager
curl -fsS http://127.0.0.1:3080/healthz
journalctl -u linkvault -n 100 --no-pager
```

Erwartung:

- `systemctl status` meldet `active (running)`.
- `/healthz` liefert `{"ok": true, "version": "0.1.0"}`.
- In `/var/lib/linkvault` wird `linkvault.sqlite3` angelegt.
- `/etc/linkvault/linkvault.env` enthaelt `LINKVAULT_DATA_DIR=/var/lib/linkvault`.
- `/etc/linkvault/linkvault.env` ist `root:linkvault` und `0640`, damit der
  Dienst das Setup-Token lesen kann, ohne es weltlesbar zu machen.

Wenn `systemctl status` schon `active (running)` meldet, `curl` aber direkt
danach noch nicht verbinden kann, ist das meist nur ein Timing-Thema. Die
aktuellen Skripte warten bis zu 60 Sekunden auf `/healthz` und geben bei einem
echten Fehler automatisch `systemctl status` und `journalctl -u linkvault` aus.

## Ein-Kommando-Smoke-Test

Alternativ:

```bash
curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-lxc-test.sh -o /tmp/linkvault-lxc-test.sh
bash /tmp/linkvault-lxc-test.sh
```

## Backup/Restore-Test im LXC

Automatischer Test vom Proxmox-Host gegen den installierten Container:

```bash
curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-backup-restore-test.sh -o /tmp/linkvault-backup-restore-test.sh
bash /tmp/linkvault-backup-restore-test.sh 112
```

Direkt als Einzeiler:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-backup-restore-test.sh)" _ 112
```

Manueller Test nach erfolgreicher Installation:

```bash
/tmp/linkvault/scripts/backup-linkvault.sh
ls -lah /var/backups/linkvault
```

Dann Restore mit dem erzeugten Archiv:

```bash
/tmp/linkvault/scripts/restore-linkvault.sh /var/backups/linkvault/linkvault-backup-*.tar.gz
curl -fsS http://127.0.0.1:3080/healthz
```

## Update-Test im LXC

Automatischer Update-Test vom Proxmox-Host gegen den installierten Container:

```bash
curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-update-test.sh -o /tmp/linkvault-update-test.sh
bash /tmp/linkvault-update-test.sh 112
```

Direkt als Einzeiler:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-update-test.sh)" _ 112
```

Der Test legt vor dem Update einen Marker-Bookmark an, fuehrt das Update aus
und prueft danach Healthcheck und Marker erneut.

## Ergebnis festhalten

Nach einem echten Testlauf bitte dokumentieren:

```text
Datum:
Proxmox-Version:
Debian-Template:
Container unprivileged:
CPU/RAM/Disk:
Installationsskript erfolgreich:
Healthcheck erfolgreich:
Backup erfolgreich:
Restore erfolgreich:
Update erfolgreich:
Offene Fehler:
```

## Letzter erfolgreicher Testlauf

```text
Datum: 2026-04-19
Host: proxbox
Kernel: Linux proxbox 6.17.13-2-pve x86_64
Debian-Template: debian-13-standard_13.1-2_amd64.tar.zst
Container-ID: 112
Container unprivileged: ja
CPU/RAM/Disk: 2 vCPU / 1024 MB / 16 GB
Installationsskript erfolgreich: ja
Healthcheck erfolgreich: ja
Erreichbare URL: http://192.168.1.132:3080
Backup erfolgreich: ja
Backup-Datei: /var/backups/linkvault/linkvault-backup-20260419-152335.tar.gz
Restore erfolgreich: ja
Restore-Marker: backup_restore_20260419152330_13602
Service nach Restore: active (running)
Healthcheck nach Restore: ja
Offene Fehler: apt/locale-Warnungen wurden beobachtet; Skripte setzen nun C.UTF-8.
```

Der erste Restore-Smoke-Testlauf traf ein Timing-/Raw-Cache-Problem beim
Neustart des Dienstes. Das Testskript wartet nun robuster auf den Healthcheck
und nutzt Cache-Buster beim Nachladen der Skripte. Danach liefen zwei
Backup/Restore-Smoke-Tests erfolgreich durch.

```text
Vorheriger erfolgreicher Restore-Marker: backup_restore_20260419152204_8110
Letzter erfolgreicher Restore-Marker: backup_restore_20260419152330_13602
```

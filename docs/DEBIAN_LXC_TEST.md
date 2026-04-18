# Debian-LXC Installationstest

## Status

Dieser Test muss auf einem echten Debian-LXC oder Proxmox-Host laufen. Auf dem
aktuellen Entwicklungsrechner wurde geprueft:

```text
OS: Darwin/macOS
Proxmox pct: nicht vorhanden
LXC tools: nicht vorhanden
Docker: nicht vorhanden
```

Darum kann der frische LXC-Test hier nicht echt ausgefuehrt werden. Die
folgenden Schritte sind die reproduzierbare Testprozedur fuer den naechsten
Lauf auf Proxmox.

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

## Ein-Kommando-Smoke-Test

Alternativ:

```bash
curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-lxc-test.sh -o /tmp/linkvault-lxc-test.sh
bash /tmp/linkvault-lxc-test.sh
```

## Backup/Restore-Test im LXC

Nach erfolgreicher Installation:

```bash
/tmp/linkvault/scripts/backup-linkvault.sh
ls -lah /var/backups/linkvault
```

Dann Restore mit dem erzeugten Archiv:

```bash
/tmp/linkvault/scripts/restore-linkvault.sh /var/backups/linkvault/linkvault-backup-*.tar.gz
curl -fsS http://127.0.0.1:3080/healthz
```

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
Offene Fehler:
```

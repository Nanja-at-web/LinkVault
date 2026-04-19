# Backup und Restore

## Ziel

Der aktuelle LinkVault-MVP speichert seine Nutzdaten in SQLite. Im
Servicebetrieb liegt die Datenbank standardmaessig hier:

```text
/var/lib/linkvault/linkvault.sqlite3
```

Die Konfiguration liegt hier:

```text
/etc/linkvault/linkvault.env
```

Die Env-Datei enthaelt das initiale Setup-Token und wird deshalb mit
`root:linkvault` und `0640` installiert. Der Dienst laeuft als User
`linkvault` und kann sie ueber die Gruppenberechtigung lesen.

Diese beiden Dateien reichen aktuell fuer ein vollstaendiges Backup des MVP.
Spaetere Archivdaten, Screenshots, PDFs oder hochgeladene Dateien werden
ebenfalls unter `/var/lib/linkvault` liegen und muessen dann mitgesichert
werden.

## Backup im laufenden Betrieb

Das Backup-Skript nutzt die SQLite-Backup-API ueber Python. Dadurch kann die
Datenbank konsistent kopiert werden, ohne den Dienst vorher zu stoppen.

```bash
sudo ./scripts/backup-linkvault.sh
```

Standardziel:

```text
/var/backups/linkvault
```

Das Skript erzeugt ein `.tar.gz` mit:

- `linkvault.sqlite3`
- `linkvault.env`, falls vorhanden

Optional kann ein anderes Zielverzeichnis gesetzt werden:

```bash
sudo LINKVAULT_BACKUP_DIR=/root/linkvault-backups ./scripts/backup-linkvault.sh
```

## Restore

Beim Restore wird der Dienst gestoppt, die bestehende Datenbank als
Zeitstempel-Datei gesichert und danach das Backup eingespielt.

```bash
sudo ./scripts/restore-linkvault.sh /var/backups/linkvault/linkvault-backup-YYYYmmdd-HHMMSS.tar.gz
```

Danach startet das Skript den Dienst wieder und ruft lokal den Healthcheck auf:

```text
http://127.0.0.1:3080/healthz
```

## Manuelle Kontrolle

Nach einem Restore:

```bash
systemctl status linkvault --no-pager
journalctl -u linkvault -n 100 --no-pager
curl http://127.0.0.1:3080/healthz
```

## Proxmox-Hinweis

Ein Proxmox-Backup des kompletten LXC ist weiterhin sinnvoll. Das
LinkVault-eigene Backup bleibt trotzdem wichtig, weil es kleiner ist und sich
leichter zwischen Installationen oder Testcontainern wiederherstellen laesst.

## Proxmox-LXC Smoke-Test

Auf dem Proxmox-Host kann ein bestehender LinkVault-Container automatisch
gegen Backup und Restore getestet werden:

```bash
LINKVAULT_CTID=112 ./proxmox/linkvault-backup-restore-test.sh
```

Oder direkt vom GitHub-Branch:

```bash
curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-backup-restore-test.sh -o /tmp/linkvault-backup-restore-test.sh
bash /tmp/linkvault-backup-restore-test.sh 112
```

Als direkter `curl | bash`-Einzeiler:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-backup-restore-test.sh)" _ 112
```

Der Test:

1. prueft `/healthz` im Container,
2. laedt Backup- und Restore-Skript in den Container,
3. legt einen temporaeren Marker-Bookmark in SQLite an,
4. erstellt ein Backup,
5. loescht den Marker,
6. stellt das Backup wieder her,
7. prueft, ob der Marker zurueck ist,
8. prueft den Healthcheck erneut.

## Noch offen

- Backup/Restore mit Archivdateien testen, sobald Archivierung implementiert
  ist.
- Restore in frischem Debian-LXC gegen `scripts/install-debian.sh` testen.
- Update-Szenario testen: Backup erstellen, Update ausfuehren, Restore als
  Fallback pruefen.

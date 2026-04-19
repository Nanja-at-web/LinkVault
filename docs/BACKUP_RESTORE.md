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

Letzter erfolgreicher echter Proxmox-LXC-Test:

```text
Datum: 2026-04-19
Container-ID: 112
Backup: /var/backups/linkvault/linkvault-backup-20260419-152335.tar.gz
Restore-Marker: backup_restore_20260419152330_13602
Healthcheck nach Restore: erfolgreich
Service nach Restore: active (running)
```

Letzter erfolgreicher Migrationstest in einen zweiten frischen Proxmox-LXC:

```text
Datum: 2026-04-19
Quelle: CT 112
Ziel: CT 114
Ziel-URL: http://192.168.1.190:3080
Backup: /var/backups/linkvault/linkvault-backup-20260419-201933.tar.gz
Restore im Ziel-CT: erfolgreich
Benutzer nach Restore: 1
Bookmarks nach Restore: 9
Healthcheck nach Restore: erfolgreich
Hinweis: Beim Dienstneustart waehrend Restore war ein frueher curl-Versuch zu
frueh; der anschliessende Healthcheck war erfolgreich.
```

## Noch offen

- Backup/Restore mit Archivdateien testen, sobald Archivierung implementiert
  ist.
- Update-Szenario testen: Backup erstellen, Update ausfuehren, Restore als
  Fallback pruefen.

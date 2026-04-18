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

## Noch offen

- Backup/Restore mit Archivdateien testen, sobald Archivierung implementiert
  ist.
- Restore in frischem Debian-LXC gegen `scripts/install-debian.sh` testen.
- Update-Szenario testen: Backup erstellen, Update ausfuehren, Restore als
  Fallback pruefen.

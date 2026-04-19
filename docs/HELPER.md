# Post-Install Helper

## Ziel

`linkvault-helper` ist das lokale Admin-Werkzeug im LinkVault-LXC. Es buendelt
die wichtigsten Betriebsaufgaben, damit Nutzer nicht manuell systemd,
journald, Backup-Skripte und Update-Skripte zusammensuchen muessen.

Der Helper wird durch `scripts/install-debian.sh` und `scripts/update-linkvault.sh`
nach `/usr/local/bin/linkvault-helper` installiert.

## Interaktives Menue

Im LinkVault-LXC:

```bash
linkvault-helper
```

Das Menue bietet:

1. Service-Status,
2. aktuelle Logs,
3. Healthcheck,
4. Backup erstellen,
5. letztes Backup wiederherstellen,
6. LinkVault aktualisieren,
7. Setup-Token anzeigen.

## Direkte Befehle

Der Helper ist auch nicht-interaktiv nutzbar:

```bash
linkvault-helper overview
linkvault-helper status
linkvault-helper logs
linkvault-helper health
linkvault-helper backup
linkvault-helper restore /var/backups/linkvault/linkvault-backup-YYYYmmdd-HHMMSS.tar.gz
linkvault-helper update
linkvault-helper token
```

Backup, Restore und Update muessen als `root` laufen.

## Noch offen

- Helper im echten CT 112 nach Update/Installation aufrufen und Ergebnis
  dokumentieren.
- Spaeter an community-scripts.org-Post-Install-Konventionen angleichen.
- Optional eine explizite Backup-vor-Update-Abfrage im Helper ergaenzen.

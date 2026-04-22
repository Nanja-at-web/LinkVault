# Update

## Schnellstart: Update im Proxmox-LXC

Wenn LinkVault mit dem Proxmox/LXC-Installer installiert wurde, ist der
einfachste Update-Befehl auf dem Proxmox-Host:

```bash
pct exec 112 -- linkvault-helper update
```

`112` ist dabei die Container-ID. Wenn dein LinkVault-Container eine andere
ID hat, entsprechend ersetzen.

Danach kurz pruefen:

```bash
pct exec 112 -- linkvault-helper health
pct exec 112 -- linkvault-helper status
```

Fuer deinen aktuellen Discovery-Endpunkt reicht also normalerweise:

```bash
pct exec 112 -- linkvault-helper update
```

Wenn du nicht sicher bist, welche CTID LinkVault hat:

```bash
pct list
```

Der Update-Smoke-Test ist etwas anderes: Er legt einen Test-Bookmark an,
fuehrt ein Update aus und prueft, ob Daten erhalten bleiben. Fuer normales
Aktualisieren reicht `linkvault-helper update`.

## Ziel

Ein installierter LinkVault-LXC soll ohne Datenverlust aktualisiert werden
koennen. Der aktuelle MVP nutzt dazu:

- `/opt/linkvault/.venv` fuer das Python-Paket,
- `/etc/linkvault/linkvault.env` fuer Konfiguration,
- `/var/lib/linkvault/linkvault.sqlite3` fuer Daten.

Das Update-Skript ersetzt nur die installierte Anwendung und die systemd Unit.
Die Datenbank und die Konfiguration bleiben erhalten.

## Update im Container

Im LinkVault-Container:

```bash
sudo ./scripts/update-linkvault.sh
```

Standardquelle:

```text
https://github.com/Nanja-at-web/LinkVault.git
```

Standard-Ref:

```text
main
```

Optional kann ein anderer Branch, Tag oder Commit getestet werden:

```bash
sudo LINKVAULT_SOURCE_REF=main ./scripts/update-linkvault.sh
```

Das Skript:

1. installiert Basiswerkzeuge wie `git`, `curl` und `python3-venv`,
2. klont die konfigurierte Quelle,
3. stoppt den Dienst,
4. installiert LinkVault neu in `/opt/linkvault/.venv`,
5. installiert die systemd Unit erneut,
6. startet den Dienst,
7. wartet auf `/healthz`.

## Proxmox-LXC Update-Smoke-Test

Auf dem Proxmox-Host kann ein bestehender LinkVault-Container automatisch
gegen ein Update getestet werden. Das ist fuer Validierung gedacht, nicht als
normaler Alltags-Update-Befehl:

```bash
LINKVAULT_CTID=112 ./proxmox/linkvault-update-test.sh
```

Oder direkt vom GitHub-Branch:

```bash
curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-update-test.sh -o /tmp/linkvault-update-test.sh
bash /tmp/linkvault-update-test.sh 112
```

Als direkter `curl | bash`-Einzeiler:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/proxmox/linkvault-update-test.sh)" _ 112
```

Der Test:

1. prueft `/healthz` im Container,
2. laedt das Update-Skript in den Container,
3. legt einen temporaeren Marker-Bookmark an,
4. fuehrt das Update aus,
5. prueft, ob der Marker noch vorhanden ist,
6. prueft den Healthcheck erneut.

## Letzter erfolgreicher echter Proxmox-LXC-Test

```text
Datum: 2026-04-19
Container-ID: 112
Quelle: https://github.com/Nanja-at-web/LinkVault.git
Ref: main
Healthcheck vor Update: erfolgreich
Update erfolgreich: ja
Healthcheck nach Update: erfolgreich
Marker erhalten: update_test_20260419193620_11553
Vorheriger erfolgreicher Marker: update_test_20260419191415_22668
Log: /tmp/linkvault-update-test.log
```

## Noch offen

- Update von einem echten alten Release auf einen neuen Release testen.
- Fallback-Ablauf dokumentieren: vor Update Backup erstellen, bei Fehler Restore
  ausfuehren.

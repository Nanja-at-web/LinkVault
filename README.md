# LinkVault

LinkVault ist der Entwurf fuer ein selbsthostbares Bookmark-, Archiv- und
Wissensverwaltungstool, das die staerksten Eigenschaften von Karakeep,
linkding, Linkwarden, LinkAce, Readeck und Shiori zusammenfuehrt.

Der Schwerpunkt liegt auf:

- sehr guter Dublettenbereinigung mit sicherem Merge statt blindem Loeschen
- Favoriten, Pins, Listen, Collections, Tags und Regeln
- automatischem Sortieren und Kategorisieren
- lokaler Archivierung von Webseiten, Artikeln, PDFs, Bildern und Notizen
- einfacher Installation als Proxmox-LXC ueber community-scripts.org
- Import aus bestehenden Bookmark-Tools und Browsern

## Dokumente

- [Produktvision](docs/PRODUCT_SPEC.md)
- [Technische Architektur](docs/ARCHITECTURE.md)
- [Dubletten, Sortierung und Kategorien](docs/DEDUP_SORTING_CATEGORIZATION.md)
- [Proxmox Community-Scripts Zielbild](docs/PROXMOX_COMMUNITY_SCRIPT.md)
- [Debian-LXC Installationstest](docs/DEBIAN_LXC_TEST.md)
- [Backup und Restore](docs/BACKUP_RESTORE.md)
- [MVP-Roadmap](docs/ROADMAP.md)

## Lokaler MVP-Prototyp

Der erste Prototyp nutzt nur die Python-Standardbibliothek. Er speichert
Bookmarks in SQLite, holt beim Speichern Metadaten aus Webseiten, normalisiert
URLs, bietet SQLite-FTS5-Volltextsuche mit Filtern und zeigt exakte
Dublettengruppen inklusive Merge-Dry-Run.

```bash
PYTHONPATH=src python3 -m linkvault.server
```

Danach ist die Mini-UI unter `http://127.0.0.1:3080` erreichbar.

Konfiguration kann lokal ueber `.env` oder im Servicebetrieb ueber
`/etc/linkvault/linkvault.env` gesetzt werden:

```env
LINKVAULT_ADDR=0.0.0.0:3080
LINKVAULT_DATA_DIR=/var/lib/linkvault
```

`LINKVAULT_DATA` kann alternativ direkt auf eine SQLite-Datei zeigen. Ohne
Konfiguration nutzt der lokale MVP `data/linkvault.sqlite3`.

## Debian-Service

Die erste Debian-Installation fuer Tests liegt in `scripts/install-debian.sh`.
Sie installiert LinkVault in eine virtuelle Python-Umgebung unter
`/opt/linkvault`, legt den Systemuser `linkvault` an, schreibt
`/etc/linkvault/linkvault.env`, nutzt `/var/lib/linkvault` als Datenpfad und
aktiviert `deploy/linkvault.service`.

```bash
sudo ./scripts/install-debian.sh
curl http://127.0.0.1:3080/healthz
```

Fuer interne LXC-Tests gibt es `proxmox/linkvault-lxc-test.sh`. Das ist noch
kein offizielles community-scripts.org-Skript, sondern der naechste
Zwischenschritt fuer reproduzierbare Proxmox-LXC-Tests.

Experimenteller Proxmox-Host-Einzeiler fuer einen neuen Debian-LXC:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/ct/linkvault.sh)"
```

Dieser Befehl wird in der Proxmox VE Shell ausgefuehrt. Er erstellt einen
neuen Debian-LXC, startet ihn und installiert LinkVault darin.

Backup und Restore fuer den SQLite-MVP:

```bash
sudo ./scripts/backup-linkvault.sh
sudo ./scripts/restore-linkvault.sh /var/backups/linkvault/linkvault-backup-YYYYmmdd-HHMMSS.tar.gz
```

Wichtige Endpunkte:

- `GET /healthz`
- `GET /api/bookmarks`
- `GET /api/bookmarks?q=suchbegriff`
- `GET /api/bookmarks?q=suchbegriff&favorite=true&pinned=true&domain=github.com&tag=selfhost&collection=Development`
- `POST /api/bookmarks`
- `GET /api/bookmarks/{id}`
- `PATCH /api/bookmarks/{id}`
- `DELETE /api/bookmarks/{id}`
- `POST /api/import/browser-html`
- `GET /api/dedup`
- `GET /api/dedup/dry-run`

## Lizenz

LinkVault steht unter AGPL-3.0-or-later. Das passt zum Ziel einer freien
Selfhost-Web-App, bei der Verbesserungen auch bei Netzwerkbetrieb wieder der
Community zugutekommen sollen.

Tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Leitidee

LinkVault soll nicht nur Links speichern. Es soll eine Link-Sammlung aktiv
pflegen: doppelte Favoriten erkennen, aehnliche Inhalte gruppieren,
schlechte Metadaten verbessern, tote Links ueberwachen und neue Links anhand
von Regeln, AI-Vorschlaegen und Nutzungsverhalten passend einordnen.

## Research

Das beigefuegte Research-Zip wurde nach
[`selfhosted-bookmark-research`](selfhosted-bookmark-research/) extrahiert.
Es enthaelt Vergleichstabellen, Projektzusammenfassungen, Quellenlisten und
erste Dedup-Beispiele.

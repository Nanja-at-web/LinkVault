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

## Sprache

- [English README](README.md)
- Deutsche README: diese Datei

## Dokumente

- [Produktvision](docs/PRODUCT_SPEC.md)
- [Technische Architektur](docs/ARCHITECTURE.md)
- [Einfluss der Deep-Research-Sammlung](docs/RESEARCH_IMPACT.md)
- [Einfluss der UX-Research-Sammlung](docs/UX_RESEARCH_IMPACT.md)
- [Einfluss der Browser- und Import-Recherche](docs/BROWSER_IMPORT_RESEARCH.md)
- [Companion-Extension-Plan](docs/COMPANION_EXTENSION.md)
- [Einfluss der Installations- und Requirements-Recherche](docs/INSTALLATION_REQUIREMENTS.md)
- [Dubletten, Sortierung und Kategorien](docs/DEDUP_SORTING_CATEGORIZATION.md)
- [Proxmox Community-Scripts Zielbild](docs/PROXMOX_COMMUNITY_SCRIPT.md)
- [Debian-LXC Installationstest](docs/DEBIAN_LXC_TEST.md)
- [Backup und Restore](docs/BACKUP_RESTORE.md)
- [MVP-Roadmap](docs/ROADMAP.md)
- [MVP Roadmap English](docs/ROADMAP.en.md)

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
linkvault-requirements
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
Der Installer gibt auch das erste Setup-Token aus. Dieses Token wird einmalig
in der Web-UI genutzt, um den initialen Admin-User anzulegen.

Der offizielle Community-Scripts-Weg bleibt stufenweise: Dieses Repo behaelt
zuerst den experimentellen Installer, neue Skript-Einreichungen sollen ueber
`community-scripts/ProxmoxVED` laufen, und spaetere Pflege kann nach Aufnahme
in `community-scripts/ProxmoxVE` erfolgen.

Backup und Restore fuer den SQLite-MVP:

```bash
sudo ./scripts/backup-linkvault.sh
sudo ./scripts/restore-linkvault.sh /var/backups/linkvault/linkvault-backup-YYYYmmdd-HHMMSS.tar.gz
```

Wichtige Endpunkte:

- `GET /healthz`
- `GET /api/setup/status`
- `POST /api/setup`
- `POST /api/login`
- `POST /api/logout`
- `GET /api/me`
- `GET /api/tokens`
- `POST /api/tokens`
- `DELETE /api/tokens/{id}`
- `GET /api/bookmarks`
- `GET /api/bookmarks?q=suchbegriff`
- `GET /api/bookmarks?q=suchbegriff&favorite=true&pinned=true&domain=github.com&tag=selfhost&collection=Development&status=active`
- `POST /api/bookmarks`
- `POST /api/bookmarks/suggestions`
- `POST /api/bookmarks/bulk`
- `GET /api/bookmarks/{id}`
- `PATCH /api/bookmarks/{id}`
- `DELETE /api/bookmarks/{id}`
- `POST /api/import/browser-html/preview`
- `POST /api/import/browser-html`
- `POST /api/import/chromium-json/preview`
- `POST /api/import/chromium-json`
- `POST /api/import/firefox-json/preview`
- `POST /api/import/firefox-json`
- `POST /api/import/safari-zip/preview`
- `POST /api/import/safari-zip`
- `GET /api/dedup`
- `GET /api/dedup/dry-run`
- `GET /api/dedup/merges`
- `POST /api/dedup/merge`

API-Token koennen API-Aufrufe mit `Authorization: Bearer <token>` oder
`X-LinkVault-Token: <token>` authentifizieren. Token-Erstellung und
Token-Loeschung brauchen weiterhin einen aktiven Browser-Login.

Importformate im MVP:

- Browser-HTML / Netscape
- Chromium-JSON fuer Chrome, Edge, Brave, Vivaldi und Opera
- Firefox-JSON aus Lesezeichen-Backups
- Safari-ZIP mit `Bookmarks.html`

Firefox-JSONLZ4 sowie generische CSV-/JSON-Importe fuer andere Bookmark-Tools
bleiben als naechste Ausbaustufen offen.

## Produktprioritaet Aus Der Recherche

Die Deep-Research-Sammlung bestaetigt: LinkVault sollte nicht einfach ein
weiterer Bookmark-Manager werden. Die staerkste Positionierung ist eine
gezielte Synthese:

- linkding als Vorbild fuer robuste URL-Deduplizierung, API und geringen
  Betriebsaufwand
- Karakeep als Vorbild fuer Favoriten, Listen, Regeln, AI-Optionen und
  moderne Wissensworkflows
- Linkwarden als Vorbild fuer Langzeitarchivierung, Collections,
  Reader-Ansicht und Annotationen
- Readeck als Vorbild fuer leichtgewichtige lokale Lesekopien, Highlights und
  EPUB/OPDS-nahe Reader-Fluesse
- LinkAce als Vorbild fuer klassische Multiuser-, SSO-, API- und
  Link-Monitoring-Reife
- Shiori/Readeck als Mahnung, den Betrieb klein und selfhost-freundlich zu
  halten
- community-scripts.org als Praxisreferenz fuer Proxmox-LXC-Installation,
  Logs, Healthcheck, Updates und Backup/Restore

Die UX-Recherche ergaenzt: Pflegeaufgaben muessen sichtbar sein, nicht in APIs
versteckt. LinkVault soll in Richtung klarer Navigation mit Inbox, Favoriten,
Dubletten, Collections, Tags, Archiv, Aktivitaet und Einstellungen wachsen.
Daraus folgen nach dem erfolgreichen echten LXC-Backup/Restore-Smoke-Test als
naechste Produktschritte URL-Duplicate-Preflight, staerkeres Dedup-Dashboard
und spaeter API-Token mit Sync-Setup. Archiv-Worker, AI und Browser-Sync kommen
danach schrittweise.

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

Die zusaetzliche Deep-Research-Sammlung vom 19.04.2026 wurde in
[Research Impact](docs/RESEARCH_IMPACT.md) ausgewertet und in Roadmap sowie
Produktprioritaet uebernommen.

Die UX-Research-Sammlung vom 19.04.2026 wurde in
[UX Research Impact](docs/UX_RESEARCH_IMPACT.md) ausgewertet. Die wichtigste
Folge: Dublettenpflege, Bulk-Organisation, Sync-Konflikte, Archivstatus und
Betriebszustand sollen eigene sichtbare Workflows werden.

Die zusaetzlichen Research-Pakete vom 20.04.2026 wurden in
[Browser and Import Research Impact](docs/BROWSER_IMPORT_RESEARCH.md)
ausgewertet. Die wichtigste Folge: Browser-Import wird als eigener,
verlustbewusster Workflow geplant. HTML bleibt der Baseline-Import; spaeter
kommen optionale Vendor-Anreicherungen, Import-Vorschau, Checksummen,
Quellmetadaten und Erhaltung unbekannter Browser-Rohdaten dazu.

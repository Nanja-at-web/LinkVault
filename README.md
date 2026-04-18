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
- [MVP-Roadmap](docs/ROADMAP.md)

## Lokaler MVP-Prototyp

Der erste Prototyp nutzt nur die Python-Standardbibliothek. Er speichert
Bookmarks in SQLite, normalisiert URLs und zeigt exakte Dublettengruppen
inklusive Merge-Dry-Run.

```bash
PYTHONPATH=src python3 -m linkvault.server
```

Danach ist die Mini-UI unter `http://127.0.0.1:3080` erreichbar.

Wichtige Endpunkte:

- `GET /healthz`
- `GET /api/bookmarks`
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

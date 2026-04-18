# ZIP-fertige Deep-Research-Sammlung zu Selfhosted Bookmark- und Archivierungs-Tools

## Executive Summary

Für den Schwerpunkt **„Dubletten bereinigen + Favoriten sortieren + kategorisieren + verwalten + synchronisieren“** ergibt sich aus den offiziellen Quellen ein ziemlich klares Bild:

- **Karakeep** ist der funktionsreichste Kandidat für moderne, automatisierte Bookmark-Workflows mit AI-Tagging, Regeln, Listen, API, Webhooks und Browser-Sync via Floccus.
- **Linkwarden** ist am stärksten, wenn **Langzeitarchivierung** und **kollaborative Sammlungen** wichtiger sind als harte Dublettenlogik.
- **linkding** ist der beste Minimalist mit sauberer URL-Prüfung, API und niedrigen Ressourcen.
- **LinkAce** ist ein klassischer, zuverlässiger Link-Archiv-Verwalter mit SSO, Monitoring und guter API, aber ohne besonders starke Duplikat-/Merge-Funktionen.
- **Readeck** ist eher ein Read-it-later-/Lesearchiv-System mit sehr niedrigen Ressourcen und guter Inhaltskonservierung.
- **Shiori** bleibt interessant als leichtgewichtiges Go-Projekt, war in dieser Sitzung aber schwerer vollständig aus Primärquellen auszuleuchten.
- Die **Community-Scripts**-Plattform für Proxmox ist kein Bookmark-Tool, aber als Deployment-Oberbau besonders relevant, weil sie bestätigte LXC-Skripte für Karakeep, Linkwarden, linkding und Readeck mit CPU-/RAM-Vorgaben bereitstellt.

## Vorgeschlagene ZIP-Struktur

```text
selfhosted-bookmark-research/
├── README.md
├── FULL_REPORT.md
├── LICENSES/
│   ├── LICENSE-NOTES.md
│   └── ATTRIBUTION.md
├── tables/
│   ├── comparison.md
│   └── comparison.csv
├── diagrams/
│   ├── entities-er.mmd
│   └── activity-timeline.mmd
├── scripts/
│   └── dedup-examples.md
└── projects/
    ├── karakeep/
    │   ├── summary.md
    │   └── raw-data.md
    ├── linkding/
    │   ├── summary.md
    │   └── raw-data.md
    ├── linkwarden/
    │   ├── summary.md
    │   └── raw-data.md
    ├── linkace/
    │   ├── summary.md
    │   └── raw-data.md
    ├── readeck/
    │   ├── summary.md
    │   └── raw-data.md
    ├── shiori/
    │   ├── summary.md
    │   └── raw-data.md
    └── community-scripts/
        ├── summary.md
        └── raw-data.md
```

## Karakeep

### Kurzfazit
Karakeep ist ein „bookmark everything“-System für Links, Notizen, Bilder und PDFs mit AI-Tagging, AI-Zusammenfassungen, Regel-Engine, Listen, RSS-Ingest, API, Webhooks, Highlights, Volltextsuche und optionaler Vollseitenarchivierung via Monolith bzw. Videoarchivierung via `yt-dlp`.

### Stärken
- sehr starker Funktionsumfang
- Favoriten, Listen, Smart Lists, Regeln, AI
- Browser-Sync via Floccus
- API, Webhooks, Mobile Apps
- ein Bookmark kann in mehreren Listen liegen, ohne dupliziert zu werden

### Schwächen
- „under heavy development“
- höhere Komplexität
- höhere Ressourcenanforderungen als linkding oder Readeck

### Vergleichspunkte
- Zweck: Bookmark-/Read-later-/Archiv-Mix mit AI
- Dubletten: ja, URL-Check vorhanden; Merge-Workflow nicht klar dokumentiert
- Favoriten/Pinning: ja
- Tags/Kategorien: ja, manuell und via AI
- Listen/Sammlungen: ja, manuell und smart
- Sync: ja
- Archivierung: stark
- Automation/AI: sehr stark
- SSO: ja
- Community-Script Default: 2 vCPU / 4 GB RAM / 10 GB Disk
- GitHub/Projektaktivität: 47 Releases, Latest 0.30.0 (01.01.2026), 162 Contributors sichtbar im Snapshot

### Offizielle Links
- Website: https://karakeep.app/
- Docs: https://docs.karakeep.app/
- Repo: https://github.com/karakeep-app/karakeep
- API: https://docs.karakeep.app/api/karakeep-api/
- Community-Script: https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/karakeep.sh

## linkding

### Kurzfazit
linkding ist das bewusst minimalistische Gegenmodell: klarer Fokus auf Lesbarkeit, einfache Einrichtung, Tags, Bulk-Editing, Multi-User, Browser-Erweiterungen, REST-API und optionale HTML-Archivierung.

### Stärken
- sehr leichtgewichtig
- saubere API
- URL-Prüfung vor dem Anlegen
- niedrige Betriebs-Last
- OIDC/Auth-Proxy-Support
- Bundles als gespeicherte Sammlungen

### Schwächen
- keine offizielle Favoriten-/Pinning-Funktion bestätigt
- weniger hierarchische Organisation
- keine AI/Automations-Tiefe wie Karakeep

### Vergleichspunkte
- Zweck: Minimaler Bookmark-Manager
- Dubletten: ja, `/api/bookmarks/check/` und Upsert-Verhalten
- Favoriten/Pinning: nein, nicht offiziell dokumentiert
- Tags/Kategorien: ja
- Listen/Sammlungen: ja, Bundles
- Sync: teilweise
- Archivierung: ja, lokale HTML-Snapshots / Wayback
- SSO: ja
- Community-Script Default: 2 vCPU / 1 GB RAM / 4 GB Disk
- Aktivität: v1.44.1 vom 11.10.2025; 9.9k Stars

### Offizielle Links
- Website/Docs: https://linkding.link/
- API: https://linkding.link/api/
- Archiving: https://linkding.link/archiving/
- Auto-tagging: https://linkding.link/auto-tagging/
- Repo: https://github.com/sissbruecker/linkding
- Community-Script: https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/linkding.sh

## Linkwarden

### Kurzfazit
Linkwarden ist das am stärksten preservation-orientierte Tool im Feld: Screenshot, PDF und Single-HTML werden pro Webseite automatisch erzeugt; dazu kommen Reader-Ansicht, Textmarker/Annotationen, Wayback-Machine-Option, lokale AI-Tagging-Option, Collections und Sub-Collections, Public Sharing und Dashboard-Pinning.

### Stärken
- stärkste Archivtiefe
- Collections + Sub-Collections
- Dashboard-Pins
- Floccus-Sync
- Browser-Extension, PWA, API-Keys, SSO
- SingleFile-Upload

### Schwächen
- Dubletten-/Merge-Logik in offizieller Doku unklar
- reale Selfhost-Issues zu Browser-Loading-Loops, Memory-Spikes, Datenverlust-/Login-Problemen

### Vergleichspunkte
- Zweck: Kollaboratives Bookmarking + Langzeitarchivierung
- Dubletten: unklar / nicht prominent dokumentiert
- Favoriten/Pinning: ja
- Tags/Kategorien: ja
- Listen/Sammlungen: sehr stark
- Sync: ja
- Archivierung: sehr stark
- Automation/AI: ja, lokales AI-Tagging
- SSO: ja
- Community-Script Default: 2 vCPU / 4 GB RAM / 12 GB Disk
- Aktivität: 16.3k Stars, 74 Contributors, 60 Releases; sichtbare Releases bis v2.13.1

### Offizielle Links
- Website: https://linkwarden.app/
- Docs: https://docs.linkwarden.app/
- Repo: https://github.com/linkwarden/linkwarden
- Dashboard/Pins: https://docs.linkwarden.app/Usage/dashboard
- Links/Data model: https://docs.linkwarden.app/Usage/links
- SingleFile-Upload: https://docs.linkwarden.app/Usage/upload-from-singlefile
- Community-Script: https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/linkwarden.sh

## LinkAce

### Kurzfazit
LinkAce ist ein klassisches Bookmark-Archiv mit Listen, Tags, Mehrbenutzerbetrieb, SSO via OAuth/OIDC, Link-Monitoring, Internet-Archive-Backups, REST-API, RSS-Feeds, Bookmarklet und Import/Export.

### Stärken
- SSO-Breite
- API-Tokens
- Monitoring toter/verschobener Links
- Kombination aus Listen und Tags
- lange Release-Historie

### Schwächen
- Archivierung eher extern orientiert (Wayback/Internet Archive)
- keine prominent dokumentierte Favoriten-/Pin-Logik
- keine starke Dubletten-Merge-Funktion sichtbar

### Vergleichspunkte
- Zweck: Selbsthostbares Link-Archiv
- Dubletten: teilweise, Import überspringt vorhandene Links
- Favoriten/Pinning: nicht belastbar bestätigt
- Tags/Kategorien: ja
- Listen/Sammlungen: ja
- Sync: teilweise
- Archivierung: ja, aber extern orientiert
- SSO: ja
- Ressourcen: keine belastbaren offiziellen Mindestwerte extrahiert
- Aktivität: v2.5.5 am 12.04.2026, 123 Releases

### Offizielle Links
- Website/Allgemein: https://www.linkace.org/docs/v1/general/
- Doku-Index: https://www.linkace.org/docs/
- Repo: https://github.com/Kovah/LinkAce
- Links: https://www.linkace.org/docs/v2/application/links/
- Import: https://www.linkace.org/docs/v2/configuration/import/
- Export: https://www.linkace.org/docs/v2/configuration/export/
- SSO: https://www.linkace.org/docs/v2/configuration/sso-oauth-oidc/
- CLI: https://www.linkace.org/docs/v2/cli/

## Readeck

### Kurzfazit
Readeck ist eine selbsthostbare Read-it-later-/Bookmark-Anwendung, die Inhalte lokal speichert, Artikel/Bilder/Videos erkennt, Labels/Favorites/Archives, Highlights, Collections, EPUB-Export, OPDS und Volltextsuche bietet.

### Stärken
- inhaltsorientierte Aufbewahrung
- geringer Ressourcenbedarf
- lokale Speicherung in ZIP-basierter Form
- EPUB/OPDS
- gut für Lesen + Archiv

### Schwächen
- Dubletten-Merge unklar
- Sync/SSO/Teamkollaboration weniger klar als bei Karakeep oder Linkwarden
- eher Leser-/Archiv-Tool als Bookmark-CRM

### Vergleichspunkte
- Zweck: Read-it-later + Bookmarking + lokale Aufbewahrung
- Dubletten: nicht belastbar bestätigt
- Favoriten/Pinning: ja
- Tags/Kategorien: ja, Labels
- Listen/Sammlungen: ja, Collections
- Sync: teilweise
- Archivierung: stark
- SSO: nicht belastbar bestätigt
- Community-Script Default: 1 vCPU / 512 MB RAM / 2 GB Disk
- Aktivität: Publikationen bis 16.04.2026 sichtbar; 84 Releases im Snapshot; 28 Sprachen im Weblate-Snapshot

### Offizielle / wichtige Links
- Website: https://readeck.org/en/
- Source/Repo: https://codeberg.org/readeck/readeck
- Go package mirror: https://pkg.go.dev/codeberg.org/readeck/readeck
- Android-App: https://github.com/jensomato/ReadeckApp
- Community-Script: https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/readeck.sh

## Shiori

### Kurzfazit
Shiori ist ein einfaches, in Go gebautes Bookmark-Manager-Projekt. In den zugänglichen Primärquellen ließen sich Repository-Metadaten, Contributor-Zahl, Container-Package-Snapshots und Release-Changelogs gut sehen; die vollständige aktuelle Feature-Darstellung war in dieser Sitzung schlechter zugänglich.

### Was belastbar bestätigt ist
- aktives Go-Projekt
- Browser-Extension-Ökosystem
- 68 Contributors im Container-Package-Snapshot
- Release-Linie 1.7.x / 1.8.x sichtbar
- Repo nennt es: „Simple bookmark manager built with Go“

### Was nicht sauber bestätigt wurde
- Favoriten/Pinning
- Dubletten-Merge
- offizielle Import-/Export-UX
- SSO-Breite
- Mobile-Apps
- Ressourcenangaben

### Offizielle Links
- Repo: https://github.com/go-shiori/shiori
- Releases: https://github.com/go-shiori/shiori/releases
- Container Package: https://github.com/orgs/go-shiori/packages/container/package/shiori
- Org/Ökosystem: https://github.com/go-shiori
- Browser-Extension: https://github.com/go-shiori/shiori-web-ext

## Community Scripts / Proxmox

### Kurzfazit
Die Proxmox-Community-Scripts-Plattform ist kein Bookmark-Manager, aber für Selfhosting-Praxis enorm wertvoll: Sie bündelt LXC-/VM-/Addon-Skripte, Website-Metadaten und Doku für inzwischen 520 Skripte in 26 Kategorien.

### Relevanz für diese Tools
Direkt bestätigt in dieser Sitzung:
- Karakeep Script
- Linkwarden Script
- linkding Script
- Readeck Script

Für LinkAce und Shiori konnte in der Sitzung kein entsprechendes Community-Script belastbar verifiziert werden.

### Offizielle Links
- Website: https://community-scripts.org/
- Doku: https://community-scripts.org/docs
- Repo: https://github.com/community-scripts/ProxmoxVE
- Gitea-Mirror: https://git.community-scripts.org/community-scripts/ProxmoxVE
- Script-Index: https://community-scripts.org/scripts

## Vergleichstabelle (Kurzform)

| Projekt | Dedup | Favoriten/Pins | Tags | Listen/Collections | Sync | Archivierung | Mobile | API | Selfhost-Ease | Docker | LXC via Community-Scripts |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Karakeep | Ja, URL-Check | Ja | Ja + AI | Ja, manuell + smart | Stark | Stark, lokal | Ja | Ja | Mittel | Ja | Ja |
| linkding | Ja, URL-/Import-Logik | Nein | Ja | Ja, Bundles | Teilweise | Ja, HTML/IA | PWA/teilweise | Ja | Sehr hoch | Ja | Ja |
| Linkwarden | Unklar | Ja | Ja | Ja, Collections + Subcollections | Stark | Sehr stark | Teilweise bis ja | Ja | Mittel | Ja | Ja |
| LinkAce | Teilweise | Nicht bestätigt | Ja | Ja | Teilweise | Teilweise | Nein bestätigt | Ja | Mittel | Ja | Nicht bestätigt |
| Readeck | Unklar | Ja | Ja, Labels | Ja, Collections | Teilweise | Stark | Android ja | Teilweise | Hoch | Ja | Ja |
| Shiori | Unklar | Unklar | Unklar | Unklar | Teilweise | Teilweise | Unklar | API-Spuren | Hoch | Ja | Nicht bestätigt |

## Lizenzhinweise

- Karakeep: AGPL-3.0
- linkding: MIT
- Linkwarden: AGPL-3.0
- LinkAce: GPL-3.0
- Readeck: AGPL-3.0
- Shiori: MIT
- Community-Scripts/ProxmoxVE: MIT

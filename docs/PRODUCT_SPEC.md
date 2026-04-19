# LinkVault Produktvision

## Ziel

LinkVault soll ein modernes Selfhost-Tool fuer Favoriten, Bookmarks,
Read-it-later-Inhalte und Webarchive werden. Es kombiniert die besten
Eigenschaften der verglichenen Tools und behebt vor allem die wiederkehrenden
Schwaechen: schwache Dublettenlogik, uneinheitliche Kategorien, fehlende
Merge-Workflows, unklare Archivkonsistenz und zu wenig Automatisierung.

## Inspirationsquellen

| Quelle | Uebernehmen | Verbessern |
|---|---|---|
| Karakeep | Links, Notizen, Assets, AI-Tags, Regeln, Listen, API, Webhooks | stabilere Admin- und Merge-Werkzeuge, klarere Datenpflege |
| linkding | Minimalismus, schnelle Bedienung, Bulk-Editing, URL-Check, REST-API | Favoriten/Pins, hierarchische Organisation, bessere Archivierung |
| Linkwarden | Collections, Sub-Collections, Sharing, lokale Archivformate, Annotationen | echte Dubletten- und Merge-Logik |
| LinkAce | Listen, Tags, Monitoring, Import/Export, SSO/OIDC | moderne Archivierung, bessere Favoriten- und Sortierfunktionen |
| Readeck | Read-it-later, lokale Inhaltskopien, Labels, Favorites, EPUB/OPDS | staerkere Bookmark-Organisation und Sync |
| Shiori | leichtes Go-Selfhosting, einfache Bedienung | vollstaendigere Team-, Archiv- und Dedup-Funktionen |

## Produktformel Aus Der Deep-Research-Sammlung

Die Deep-Research-Sammlung vom 19.04.2026 schaerft die Produktlinie:

```text
linkding-artige URL-Deduplizierung
+ Karakeep-artige Favoriten, Listen, Regeln und AI-Optionen
+ Linkwarden-artige Archivformate und Collections
+ Readeck-artige Reader-/Highlight- und leichte Speicherlogik
+ LinkAce-artige Multiuser-, SSO-, API- und Monitoring-Reife
+ Shiori-artige Einfachheit im Betrieb
+ community-scripts-artige Proxmox-LXC-Installation
```

Damit ist LinkVaults Kernversprechen nicht "alle Features sofort", sondern:
sichere Link-Pflege, starke Favoriten-/Dublettenbereinigung, gute
Selfhost-Betriebsqualitaet und schrittweise Archivtiefe.

## Kernfunktionen

### Bookmarks und Inhalte

- Link-Bookmarks mit Titel, Beschreibung, Screenshot, Favicon, Sprache,
  Autor, Publisher, Lesedauer und Inhaltstyp.
- Textnotizen, PDFs, Bilder und hochgeladene Dateien als gleichwertige Items.
- Reader-Ansicht mit Volltext, Highlights, Notizen und Zitaten.
- Versionierte Archivierung: Live-URL, Reader-Extrakt, Screenshot, PDF,
  Single-HTML und optional WARC.
- Link Health Checks: erreichbar, Weiterleitung, Zertifikatsfehler, 404,
  Soft-404, Inhalt geaendert.

### Favoriten und Pins

- `favorite`: persoenlicher Favorit.
- `pin`: sichtbar hervorgehobener Link auf Dashboard oder Collection.
- `priority`: niedrig, normal, hoch, kritisch.
- `read_status`: unread, reading, done, archived.
- Mehrere Favoritenansichten: alle Favoriten, kuerzlich favorisiert,
  haeufig geoeffnet, ungelesene Favoriten, kaputte Favoriten.

### Kategorien, Tags und Collections

- Collections als Ordnerstruktur mit Sub-Collections.
- Tags als flexible, mehrfache Labels.
- Smart Collections mit gespeicherten Suchfiltern.
- Bundles fuer kuratierte Link-Sets.
- Regeln: Wenn Domain, Inhaltstyp, Text, Sprache, Autor oder Tag passt,
  dann Collection/Tag/Favorit/Prioritaet setzen.
- AI-Vorschlaege fuer Tags, Titel, Zusammenfassung, Collection und
  Dublettengruppe, aber mit nachvollziehbarer Begruendung.

### Dublettenbereinigung

LinkVault behandelt Dubletten als Datenpflege-Workflow, nicht als
Ein-Klick-Risiko.

- Exakte URL-Dubletten nach kanonisierter URL.
- Near-Duplicates nach Weiterleitung, Canonical-Link, Inhaltshash,
  Titel-Aehnlichkeit und Domain/Slug-Aehnlichkeit.
- Merge-Kandidaten mit Score und Grund.
- Dry-Run vor jeder Massenaktion.
- Siegerregeln: Favorit > Pin > mit Highlights > mit Notizen > mit Archiv >
  aelterer Originaleintrag > haeufiger genutzt.
- Merge uebernimmt Tags, Collections, Notizen, Highlights, Archivdateien,
  Favoritenstatus, Pins und Importquellen.
- Undo-Log fuer Merge- und Loeschaktionen.

### Suche und Sortierung

- Volltextsuche ueber Titel, URL, Textinhalt, Notizen, Tags und OCR-Text.
- Sortierung nach Relevanz, Aktualitaet, Lesedauer, Domain, Collection,
  Favorit, Health-Status, Nutzungsfrequenz und manueller Reihenfolge.
- Facetten: Tag, Collection, Domain, Sprache, Autor, Inhaltstyp, Status,
  Importquelle, Archivstatus.
- Saved Searches und Smart Collections.

### Import, Export und Sync

- Browser-Bookmark-HTML.
- Netscape Bookmark Format.
- CSV und JSON.
- Importprofile fuer Karakeep, linkding, Linkwarden, LinkAce, Readeck und
  Shiori, sofern deren Exporte/API-Zugriffe verfuegbar sind.
- WebDAV/OPDS fuer Lesefluss.
- Floccus-kompatible Bridge als spaetere Ausbaustufe.
- REST-API und Webhooks fuer Automatisierung.

### Benutzer, Rechte und Selfhost

- Einzelbenutzer-Modus als Default.
- Multi-User mit Rollen: owner, admin, editor, reader.
- OIDC/OAuth2 und Reverse-Proxy-Auth.
- Public Sharing fuer Collections oder einzelne Links.
- Audit-Log fuer Import, Merge, Delete, Share und Admin-Aktionen.

## Nicht-Ziele fuer Version 1

- Kein Social-Network-Feed.
- Keine Cloud-Pflicht.
- Keine proprietaeren AI-Abhaengigkeiten.
- Keine aggressive automatische Loeschung ohne Dry-Run und Undo.

## Quellenlage

Die lokale Research-Sammlung liegt unter
[`selfhosted-bookmark-research`](../selfhosted-bookmark-research/). Zusaetzlich
wurde am 18.04.2026 geprueft:

- Community-Scripts beschreibt LXC-Container-Skripte als Einstiegspunkt unter
  `ct/*.sh`, die auf dem Proxmox-Host laufen und ein
  `install/*.sh`-Skript im Container ausfuehren.
- Das Community-Scripts-Repository nennt Proxmox VE 8.4, 9.0 und 9.1 als
  aktuelle Zielversionen und beschreibt Default/Advanced-Installationsmodi.
- Linkwarden dokumentiert Links, Tags und Collections als Kerndatenmodell,
  wobei Links genau einer Collection gehoeren koennen und mehrere Tags haben.
- Karakeep dokumentiert eine API fuer Bookmarks, Listen, Tags, Highlights,
  Assets und Backups.

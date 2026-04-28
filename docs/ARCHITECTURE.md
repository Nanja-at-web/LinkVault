# Technische Architektur

## Architekturleitbild

LinkVault ist im Kern eine **leichtgewichtige, selfhost-taugliche Bookmark-, Favoriten-, Link-Management- und Sync-Plattform**.

Die Architektur muss zuerst diese Kernaufgaben unterstützen:

- Bookmarks schnell speichern und bearbeiten
- Favoriten verwalten
- Tags, Listen und Collections organisieren
- große Link-Bibliotheken filtern, durchsuchen und sortieren
- Dubletten sicher erkennen, prüfen, zusammenführen und optional entfernen
- Browser- und Tool-Importe sauber verarbeiten
- Import-/Restore-/Sync-Konflikte nachvollziehbar behandeln
- zuverlässig auf Proxmox VE / Debian LXC laufen

## Bewusste Abgrenzung

LinkVault ist **architektonisch nicht primär**:

- ein Read-later-System
- ein Reader-first-Produkt
- ein Archivierungs-Stack mit schwerem Worker-Zwang
- ein Multi-Service-Plattformprodukt im MVP
- eine AI- oder Crawler-zentrierte Anwendung

Archivierung, Reader-Funktionen, Screenshots/PDF oder externe Worker dürfen später wachsen, aber **nicht** den Core dominieren.

---

## Betriebsphilosophie

Der Standardpfad von LinkVault bleibt **klein, robust und LXC-freundlich**.

Die Architektur folgt daher einem **Core-first-Modell**:

### Core MVP
Pflichtbestandteile:
- Bookmark-Verwaltung
- Login / Auth
- SQLite
- FTS5
- Favoriten / Tags / Listen / Collections
- Suche / Filter / Sortierung
- Dedup / Duplicate Preflight / Dedup Center
- Import / Export
- Backup / Restore
- Update
- Companion Extension
- Proxmox-/Debian-LXC-tauglicher Betrieb

### Optionale spätere Profile
Nur nachrangig und optional:
- Archive Worker
- Reader-Extrakte
- Screenshot / PDF / Single-HTML
- AI-Vorschläge
- externe Suchdienste
- Plattformmodus für größere Installationen

### Grundsatz
Der Core muss alleine nützlich, schnell und stabil sein.

Schwere Zusatzprofile dürfen:
- separat aktiviert werden
- zusätzliche Dienste benötigen
- mehr Ressourcen brauchen

Sie dürfen aber **nicht** Voraussetzung für den normalen Bookmark-Betrieb sein.

---

## Empfohlener Stack

### Aktueller Kern
- **Backend:** Python
- **Datenbank:** SQLite
- **Suche:** SQLite FTS5
- **Deployment:** Proxmox VE / Debian LXC
- **Companion:** Firefox WebExtension
- **Tests:** stdlib `unittest`

### Architekturregel
Die bestehende Python/SQLite-Architektur ist der aktuelle Standardpfad.

LinkVault soll **nicht ohne ausdrückliche Neuentscheidung** auf:
- Go
- TypeScript/Node
- PostgreSQL
- Redis
- externe Search-Stacks
umgelenkt werden.

### Spätere optionale Erweiterungen
Nur bei echtem Bedarf:
- optionaler Worker-Prozess für Archivierung
- optionale externe Suche bei sehr großen Installationen
- optionale Queue-Erweiterung
- optionale alternative Release-Artefakte

### Grundsatz
Erst den Bookmark-Kern gut machen, dann schwere Technik ergänzen.

---

## Architekturprinzipien

### 1. Bookmark-first
Alle Kernmodule und Datenflüsse müssen zuerst den Bookmark- und Favoriten-Workflow unterstützen.

### 2. Safe by default
Dubletten, Importe, Konflikte und Sync-nahe Änderungen dürfen nie blind destruktiv arbeiten.

### 3. Lightweight self-hosting
Keine unnötigen Pflichtdienste im MVP.

### 4. Erweiterbarkeit ohne Drift
Spätere Funktionen dürfen angebaut werden, ohne den Kern in ein Reader-/Archivprodukt zu verwandeln.

### 5. Datenbewahrung bei Merge und Import
Wichtige Metadaten dürfen nicht unnötig verloren gehen.

---

## Module

| Modul | Aufgabe |
|---|---|
| `ingest` | URL speichern, normalisieren, Metadaten laden, Redirects/Candidate-Daten vorbereiten |
| `bookmarks` | Bookmark-CRUD, Favoriten, Pins, Status, Listen-/Collection-/Tag-Zuordnung |
| `dedup` | Duplicate Preflight, Kandidatenbildung, Scores, Merge-Plan, Review, Undo |
| `organize` | Regeln, Bulk-Edit, Saved Views, Sortierung, Kategorisierung |
| `search` | Volltextsuche, Filter, Sortierung, gespeicherte Ansichten |
| `importer` | Browser-/HTML-/CSV-/JSON-/Tool-Importe mit Vorschau und Konfliktlogik |
| `sync` | sync-nahe Import-/Restore-/Konfliktflüsse, Snapshot-/Drift-Logik |
| `api` | REST-Endpunkte, Extension-Schnittstellen, Tokens |
| `auth` | lokale Nutzer, Rollen, API-Tokens, Passwortwechsel/-reset |
| `admin` | Jobs, Logs, Backups, Updates, Diagnose |
| `health` | Link-Checks, Redirect-/Dead-Link-Prüfung, Pflegehinweise |
| `archive` | optionales späteres Modul für Reader-/Screenshot-/PDF-/Single-HTML-Funktionen |

## Modulregel

`archive` ist **nicht** Teil des verpflichtenden Kernbetriebs.  
Die Kernidentität von LinkVault entsteht aus:
- `bookmarks`
- `dedup`
- `organize`
- `search`
- `importer`
- `sync`

---

## Import-Architektur

Die Import-Architektur folgt einer klaren, nicht-destruktiven Schichtung:

```text
source file / API
  -> parser
  -> canonical import record
  -> duplicate preflight
  -> import preview
  -> merge/create/update plan
  -> committed bookmark records

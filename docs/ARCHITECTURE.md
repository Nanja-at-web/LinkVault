# Technische Architektur

## Empfohlener Stack

LinkVault sollte als robuste, LXC-freundliche Web-App gebaut werden:

- Backend: Go oder TypeScript/Node. Empfehlung: Go fuer kleine Binaries,
  einfache LXC-Installation und Shiori-aehnliche Leichtigkeit.
- Frontend: React mit serverseitig ausgeliefertem Build.
- Datenbank: SQLite fuer den Python-MVP, PostgreSQL spaeter als Default.
- Suche: SQLite FTS5 im Python-MVP, spaeter PostgreSQL Full Text Search,
  Meilisearch oder Tantivy-basierter Index.
- Queue: eingebaute Job-Tabelle fuer MVP, spaeter Redis optional.
- Archivierung: Readability-Extraktion, Single-HTML, Screenshot/PDF ueber
  Playwright oder Browserless-kompatiblen Worker.
- AI: Provider-Abstraktion. Lokal via Ollama/OpenAI-kompatible API,
  remote optional, komplett abschaltbar.

## Module

| Modul | Aufgabe |
|---|---|
| `ingest` | URL speichern, Metadaten laden, Redirects verfolgen, Canonical URL bestimmen |
| `archive` | Reader-Text, Screenshot, PDF, Single-HTML, Assets speichern |
| `dedup` | Fingerprints, Kandidaten, Scores, Merge-Plan, Undo |
| `organize` | Regeln, AI-Vorschlaege, Smart Collections, Bulk-Edit |
| `search` | Volltextindex, Facetten, gespeicherte Suche |
| `health` | Link-Checks, Dead-Link-Erkennung, Redirect-Historie |
| `importer` | Browser/HTML/CSV/JSON/API-Importe |
| `api` | REST, Webhooks, API-Keys |
| `auth` | lokale Nutzer, OIDC, Reverse-Proxy-Auth |
| `admin` | Jobs, Logs, Backups, Updates, Diagnose |

## Import-Architektur

Das Browser-API-Research vom 20.04.2026 fuehrt zu einer klaren
Import-Schichtung:

```text
source file / API
  -> parser
  -> canonical import record
  -> duplicate preflight
  -> import preview
  -> merge/create/update plan
  -> committed bookmark records
```

Netscape-HTML ist die gemeinsame Baseline. Vendor-Formate sollen nur
zusaetzlich anreichern:

- Chromium-Familie: HTML plus optionales Chromium-JSON.
- Firefox/Tor Desktop: HTML plus optionales JSON/JSONLZ4.
- Safari: ZIP mit `Bookmarks.html` plus optionale Metadaten.
- Samsung Internet und DuckDuckGo Browser: zuerst als eingeschraenkte
  Importquellen, keine allgemeine Bookmark-API voraussetzen.

Unbekannte Felder werden nicht verworfen. Sie landen in `raw_vendor_payload`
oder in einem spaeteren Import-Record, damit LinkVault bei Importen keine
Browserdaten kaputt normalisiert.

## Datenmodell

```text
users
  id, email, display_name, role, auth_provider, created_at

items
  id, owner_id, type, title, url, canonical_url, normalized_url,
  description, content_hash, domain, language, author, publisher,
  favorite, pinned, priority, read_status, created_at, updated_at

collections
  id, owner_id, parent_id, name, description, color, visibility

item_collections
  item_id, collection_id, position, pinned

tags
  id, owner_id, name, normalized_name, color

item_tags
  item_id, tag_id, source

archives
  id, item_id, kind, storage_path, content_hash, byte_size, created_at

import_sessions
  id, owner_id, source_name, source_format, source_file_name,
  source_file_checksum_sha256, sync_origin, imported_at,
  created_count, duplicate_count, conflict_count, raw_summary_json

import_records
  id, session_id, item_id, source_browser, source_profile, source_device,
  source_path, source_id, source_guid, parent_source_id, url_raw,
  url_normalized, added_at, modified_at, last_used_at,
  is_reading_list, is_speed_dial, is_mobile_root, is_managed,
  raw_vendor_payload

highlights
  id, item_id, user_id, text, note, locator, color, created_at

dedup_candidates
  id, group_id, item_a_id, item_b_id, score, reasons, state

merge_actions
  id, group_id, winner_item_id, merged_item_ids, plan_json,
  undo_json, actor_id, created_at

rules
  id, owner_id, name, enabled, trigger_json, action_json, priority

jobs
  id, kind, payload_json, state, attempts, last_error, created_at, updated_at
```

## URL-Normalisierung

Die Normalisierung muss deterministisch und sichtbar sein:

- Scheme lowercasen, Default-Port entfernen.
- Host lowercasen, `www.` optional als Aehnlichkeitsmerkmal behandeln.
- Tracking-Parameter entfernen: `utm_*`, `fbclid`, `gclid`, `mc_cid`,
  `igshid` und konfigurierbare weitere Parameter.
- Fragment entfernen, ausser es ist fuer bestimmte Domains relevant.
- Trailing Slash normalisieren.
- Redirect-Ziel und HTML-Canonical getrennt speichern.

## Dedup-Score

```text
score = exact_normalized_url * 100
      + same_redirect_target * 90
      + same_canonical_url * 85
      + same_content_hash * 80
      + title_similarity * 40
      + slug_similarity * 35
      + same_domain * 15
      - conflicting_content_type * 30
```

Score-Bedeutung:

- `>= 95`: automatisch als sichere Dublettengruppe vorschlagen.
- `80-94`: Review erforderlich.
- `60-79`: nur als "moeglicherweise aehnlich" anzeigen.
- `< 60`: keine Dublette.

## Merge-Sicherheit

Jeder Merge erzeugt einen Plan:

```json
{
  "winner": "item_123",
  "merge": ["item_456", "item_789"],
  "move_tags": true,
  "move_collections": true,
  "move_highlights": true,
  "move_archives": true,
  "keep_redirect_history": true,
  "delete_losers": false
}
```

Default ist `delete_losers: false`: Verlierer werden zuerst als
`merged_into` markiert. Endgueltiges Loeschen ist ein separater Cleanup-Job.

## LXC-Betrieb

Aktueller Python-MVP:

- Debian 13 LXC
- systemd Service `linkvault`
- Konfiguration ueber `/etc/linkvault/linkvault.env`
- App unter `/opt/linkvault`
- Daten unter `/var/lib/linkvault/linkvault.sqlite3`
- Logs ueber journald/stdout
- Healthcheck ueber `/healthz`

Spaeteres Default-Ziel:

- Debian 13 LXC
- 2 vCPU
- 4096 MB RAM
- 16 GB Disk fuer kleine Archive
- PostgreSQL lokal im Container
- optionaler Browser/Archive-Worker im selben Container fuer einfache
  Installation

Groessere Installationen sollten Archivspeicher und Worker trennen koennen.

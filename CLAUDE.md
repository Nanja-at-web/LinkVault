# CLAUDE.md — LinkVault

> Operational project context for Claude Code and AI coding assistants.
> Last updated: 2026-04-28

---

## Project overview

**LinkVault** — self-hosted bookmark, favorites, link-management and sync platform.

**GitHub:** github.com/Nanja-at-web/LinkVault  
**Stack:** Python 3.13 · SQLite + FTS5 · stdlib-only · Firefox WebExtension companion  
**License:** AGPL-3.0  
**Deploy target:** Proxmox VE, Debian 12 LXC (community-scripts.org one-liner pattern)  
**Primary dev language (sessions):** German

**Canonical Windows repo path:**  
`<PRIVATE_PATH>\Documents\git\LinkVault\LinkVault\`

---

## Product mission (highest-priority steering rule)

LinkVault is primarily a **self-hosted bookmark / favorites / link manager with synchronization**.

Its main job is to help users:

- save links quickly
- manage bookmarks and favorites
- organize links via tags, lists and collections
- sort, filter and search efficiently
- bulk-edit and clean up bookmark libraries
- detect, review, merge and optionally remove duplicates safely
- import/export bookmark data reliably
- synchronize bookmark state across browser / extension / server workflows

### LinkVault is NOT primarily:

- a read-later app
- a reader-first product
- a content-consumption platform
- a note-taking-first tool
- a knowledge-base-first tool
- an archive-first product

Read-later or archival functions may exist later as optional supporting features, but they must not dominate product direction, navigation, UI, roadmap order or terminology.

If any roadmap item, old summary or historical note conflicts with this mission, **this mission wins** until the docs are updated.

---

## Core product pillars

### 1. Bookmark management
Core entities and workflows must revolve around:
- bookmarks
- favorites
- tags
- lists
- collections
- inbox / triage
- archive (secondary)
- duplicate review
- import / export
- sync state

### 2. Favorites-first usability
Favorites must be a first-class concept:
- dedicated favorites view
- quick favorite toggle
- favorite filter
- bulk favorite operations
- visible favorite status in list and detail views

### 3. Organization-first workflows
Users must be able to:
- assign tags
- assign one bookmark to multiple lists/collections where appropriate
- move or copy bookmarks between organizational structures
- save filtered views
- use quick-add with sensible defaults
- perform bulk operations without friction

### 4. Duplicate handling is a core feature
Duplicate handling is not an afterthought.

Required long-term direction:
- duplicate preflight on save/import/sync
- duplicate review center
- exact URL match
- normalized URL match
- domain/path-level candidate grouping where useful
- dry-run before applying changes
- safe merge flow
- preserve data unless explicit destructive removal is confirmed
- optional explicit removal after review
- never delete blindly

Default philosophy:
- safe by default
- reviewable before apply
- user can merge / keep separate / archive / remove

### 5. Synchronization and migration
Sync/import/export are core product capabilities, not side ideas.

This includes:
- browser import
- extension-assisted flows
- restore/import conflict handling
- long-term sync architecture
- metadata preservation where feasible

---

## Design benchmarks

Use these as product references:

| Tool | Role |
|---|---|
| Karakeep | Primary functional benchmark: lists, organization, automation, feature breadth |
| Linkwarden | Collections / sharing / structured dashboard benchmark |
| linkding | Minimalism / speed / search-first benchmark |
| LinkAce | Classic bookmark-management and visibility model reference |
| Readeck | Lightweight operation / migration reference, but NOT read-later product direction |
| Shiori | Lightweight bookmark-manager reference |

Important:
- Do not turn LinkVault into a Readeck/Wallabag/Omnivore-style reader-first product.
- Borrow strengths, not product identity drift.

---

## UI / UX / GUI direction

UI/GUI for bookmark management is a product-critical concern.

Do NOT treat UI as superficial polish only.

### Required UI direction
LinkVault should feel closer to:
- Karakeep
- Linkwarden
- linkding
than to a read-later article reader.

### UI priorities
- clear sidebar or similarly strong navigation
- strong bookmark list / grid / detail model
- visible search and filters
- visible favorites handling
- visible tags / lists / collections
- clear bulk actions
- clear duplicate review entry point
- quick-add and inbox workflow
- usable admin/profile/settings separation
- practical, not decorative design

### Usability rule
Prefer:
- fast workflows
- low-friction interactions
- understandable information architecture
- explicit status indicators
- clear feedback
over visual novelty.

### Important distinction
“UI polish” may be secondary to broken core functionality, but:
- navigation
- layout structure
- bookmark-management operability
- dedup interaction quality
- search/filter clarity
are **not optional polish**.
They are core product quality.

---

## Current product priorities

At the start of each session, check:
- `docs/ROADMAP.md`
- `docs/linkvault_statusanalyse.md`

But interpret them through the product mission in this file.

### Immediate priorities
1. Strengthen bookmark-management-first UI/navigation
2. Finish and improve favorites / tags / lists / collections workflows
3. Improve quick-add and inbox triage
4. Strengthen duplicate review / merge / safe-remove flows
5. Expand import/export and migration coverage
6. Strengthen sync-oriented conflict handling where it supports bookmark workflows
7. Continue Proxmox / installer quality after product-core gaps are closed

### Important note
Conflict Center is useful, but it must support the bookmark product.
It must not become the product identity.

---

## Parked items / scope control

These are not forbidden forever, but must not displace bookmark-core work without explicit request:

- Team / Shared Collections
- SCIM / IdP provisioning
- Go migration
- heavy enterprise provisioning
- archive-first / reader-first expansion
- broad knowledge-base functionality

### Browser import engine
Browser import is **not** a forbidden feature.
It is a core planned capability.
If not currently being implemented, treat it as:
- planned
- important
- roadmap-bound
- not to be forgotten

---

## Architecture notes

- **Backend:** Pure Python, no framework, no build step. Runs as `python -m linkvault.server`
- **Database:** SQLite only. FTS5 for full-text search. No Postgres
- **Auth:** `src/linkvault/auth.py` — `admin` / `user` roles, user-bound tokens, password change/reset
- **Settings:** `user_settings` key-value table in SQLite
- **Dedup:** safe reviewable dedup logic, no blind destructive actions
- **Extension:** Firefox WebExtension companion
- **Sync/import/restore conflicts:** useful, but must remain subordinate to bookmark workflows

---

## Key files and directories

```text
src/linkvault/
  server.py
  store.py
  auth.py
  metadata.py
  config.py

extensions/linkvault-companion/
  popup.js
  shared.js
  styles.css
  manifest.json

tests/
  test_store.py
  test_auth.py
  test_server_html.py
  test_extension_assets.py
  test_docs.py

docs/
  ROADMAP.md / ROADMAP.en.md
  linkvault_statusanalyse.md
  ADMIN_PROFILE_SHARING_PATTERNS.md
  ROADMAP_SOLUTIONS.md
  DEVELOPMENT_WINDOWS.md

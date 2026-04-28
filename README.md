# LinkVault

LinkVault is a self-hosted bookmark, favorites and link-management platform with strong duplicate handling, import/export workflows and lightweight Proxmox-friendly deployment.

## What LinkVault is

LinkVault is built for people who want to:

- save links quickly
- manage bookmarks and favorites
- organize large link libraries with tags, lists and collections
- search, filter and sort efficiently
- detect, review, merge and optionally remove duplicates safely
- import bookmarks from browsers and other tools
- keep the whole system self-hosted on lightweight infrastructure

## What LinkVault is not

LinkVault is **not primarily**:

- a read-later app
- a reader-first product
- a web archive as the main product
- a knowledge base
- a note-taking tool with bookmark side functionality

Archive or reader-style features may exist later as optional extensions, but they are not the main product direction.

---

## Why LinkVault exists

Most self-hosted bookmark tools force a trade-off:

- either lightweight and simple
- or feature-rich but heavier and less focused on cleanup and migration

LinkVault aims to close that gap.

Its main product strengths are:

- strong bookmark and favorites management
- visible duplicate review and cleanup
- clean import/export and migration workflows
- browser-aware metadata handling
- safe, reviewable merge behavior
- lightweight self-hosted operation on Proxmox VE / Debian LXC

---

## Current focus

The current product focus is:

- bookmark storage and editing
- favorites, pins, tags, collections and notes
- full-text search with SQLite FTS5
- bulk actions
- duplicate preflight before save
- duplicate review, dry-run and merge without blind deletion
- import preview and migration safety
- browser companion workflows
- Proxmox-friendly install / update / backup / restore

---

## Current feature set

### Bookmark management
- save links with URL normalization
- fetch metadata such as title, description, favicon and domain
- edit bookmarks in the UI
- manage favorites and pins
- add tags, collections and notes
- work with Inbox-style unsorted bookmarks
- use saved views and multiple display modes

### Search, filtering and organization
- SQLite FTS5 full-text search
- filters for favorites, pins, domain, tags, collections and status
- compact, detailed and grid-style bookmark views
- bulk actions for tags, collections, favorites and pins

### Duplicate handling
- exact duplicate detection
- normalized URL duplicate detection
- duplicate preflight before save
- duplicate dashboard with dry-run
- winner suggestion and field comparison
- merge without blind hard delete
- merge history / undo direction
- marked merged duplicates instead of silent destructive cleanup

### Import and migration
- browser HTML import preview
- Chromium JSON import path
- import session metadata
- duplicate and conflict awareness during import
- provenance-aware import direction for future migration breadth

### Companion extension
- save current tab
- read browser bookmarks
- send bookmark previews to LinkVault
- safe browser re-import with preview
- duplicate-aware and conflict-aware browser round-trips

### Self-hosting and operations
- Python + SQLite + FTS5 core
- Proxmox VE / Debian LXC friendly deployment
- helper commands for health, update, backup and restore
- documented update path
- documented backup / restore path
- real LXC smoke-test direction

---

## Product direction

LinkVault is being built around five core pillars:

1. Bookmark management
2. Favorites as a first-class concept
3. Strong organization with tags, lists and collections
4. Safe duplicate review and cleanup
5. Import/export and sync-adjacent browser workflows

Everything else is secondary.

---

## Duplicate philosophy

LinkVault treats duplicate handling as a real product feature, not just an import warning.

### Core principles
- detect duplicates early
- show review before risky actions
- preserve useful metadata during merge
- do not delete blindly
- keep cleanup understandable
- support large-library maintenance

### Merge behavior
When merging duplicates, LinkVault is designed to preserve important data such as:
- favorites
- tags
- collections
- notes
- better metadata
- import/source context

---

## Import philosophy

Import is not just “upload a file”.

For LinkVault, import means:

- preview first
- detect duplicates
- surface conflicts
- keep provenance
- preserve metadata where feasible
- avoid silent destructive outcomes

HTML remains the common baseline.  
Richer browser-specific formats can be layered on top as enrichment.

---

## Self-hosting philosophy

LinkVault is intentionally designed to stay practical for small self-hosted installations.

### Default path
- lightweight
- SQLite-based
- single-service-friendly
- easy to back up
- easy to restore
- easy to update
- realistic for Proxmox homelab use

### Heavy optional features
Heavier topics such as archive workers, screenshots/PDF, reader extraction, AI helpers or larger service topologies are later optional extensions, not default requirements.

---

## Tech stack

Current core stack:

- Python
- SQLite
- SQLite FTS5
- custom backend runtime
- Firefox companion extension
- Proxmox VE / Debian LXC deployment path
- stdlib-first testing approach

---

## Project status

LinkVault is under active development.

The technical foundation is already strong in:
- bookmark storage
- dedup logic
- import preview direction
- browser companion groundwork
- Proxmox installation path
- backup / restore / update workflows

The biggest remaining visible product gap is still the main UI/GUI clarity for:
- navigation
- favorites
- organization
- duplicate maintenance
- everyday bookmark flows

---

## Documentation

Important documents:

- `ROADMAP.md`
- `ROADMAP.en.md`
- `PROJECT_MEMORY.md`
- `docs/linkvault_statusanalyse.md`
- `PRODUCT_SPEC.md`
- `ARCHITECTURE.md`
- `RESEARCH_IMPACT.md`
- `UX_RESEARCH_IMPACT.md`
- `COMPANION_EXTENSION.md`
- `COMPANION_EXTENSION_UPDATE.md`
- `DUPLICATE_PREFLIGHT.md`
- `DEDUP_SORTING_CATEGORIZATION.md`
- `PROXMOX_COMMUNITY_SCRIPT.md`
- `BACKUP_RESTORE.md`
- `UPDATE.md`
- `HELPER.md`

---

## Development priorities

Current high-priority themes:

- bookmark-centered navigation
- Quick Add
- favorites / tags / lists / collections workflows
- Duplicate Center UX
- broader import / export / migration coverage
- stable browser round-trips
- continued Proxmox operational maturity

Lower-priority themes:

- reader mode
- archive-heavy flows
- screenshot / PDF / single-HTML
- AI summaries
- heavy multi-service expansion
- enterprise provisioning

---

## Intended users

LinkVault is especially aimed at people who want:

- self-hosting
- bookmark control
- browser migration support
- duplicate cleanup
- favorites management
- Proxmox-friendly deployment
- a focused system that stays practical

---

## Guiding question

For every major decision, LinkVault asks:

**Does this make the product better as a self-hosted bookmark, favorites, organization, duplicate-cleanup, import/export and sync-capable platform?**

If the answer is mainly “it makes LinkVault more of a reader or archive product”, the direction is wrong.

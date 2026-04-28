# PROJECT_MEMORY.md

> Generated: 2026-04-28
> Purpose: Consolidated project memory for LinkVault.
> Authority rule:
> - Current product mission and steering are defined by `CLAUDE.md`
> - `docs/ROADMAP.md` and `docs/linkvault_statusanalyse.md` are the current operational planning documents
> - Historical batch summaries remain implementation history, not product mission
>
> If older summaries, archived notes or research exports conflict with this file, this file and `CLAUDE.md` win.

---

## Overview

LinkVault is a **self-hosted bookmark, favorites, link-management and sync platform** built in Python and designed for Proxmox LXC deployment.

Development began on 2026-04-18.  
Implementation work has been heavily AI-assisted, but the project direction is now explicitly normalized around **bookmark management first**.

### Important correction

LinkVault is **not primarily**:
- a read-later product
- a reader-first app
- a content-consumption platform
- a knowledge-base-first app
- an archive-first product

Archival or reading-related capabilities may exist later as supporting features, but they must not dominate the mission, navigation, feature order, language, or interface structure.

---

## Product mission

LinkVault exists primarily to help users:

- save links quickly
- manage bookmarks and favorites
- organize links with tags, lists and collections
- sort, filter and search efficiently
- bulk-edit bookmark libraries
- detect, review, merge and optionally remove duplicates safely
- import and export bookmark data reliably
- synchronize bookmark state across browser, extension and server workflows
- run the whole system self-hosted on lightweight infrastructure

### Core identity

LinkVault is primarily a:

- bookmark manager
- favorites manager
- link organization tool
- sync-aware self-hosted platform

### Non-primary areas

The following are explicitly secondary:

- article reading experience
- read-later workflows
- content consumption UX
- archive-first product positioning
- note-taking-first product logic
- knowledge-base-centric expansion

---

## Key product pillars

### 1. Bookmark management first

Core flows must focus on:

- bookmarks
- favorites
- inbox / triage
- tags
- lists
- collections
- filters
- saved views
- quick-add
- bulk actions
- import / export
- synchronization
- duplicate handling

### 2. Favorites are first-class

Favorites are not a side flag.
They are a core organizational concept and should support:

- dedicated favorites view
- quick toggle
- filters
- bulk changes
- visible status in list and detail views

### 3. Organization is central

Users must be able to:

- assign and remove tags quickly
- sort and filter efficiently
- place bookmarks into lists / collections
- save filtered views
- review inbox-style unorganized links
- perform bulk changes without friction

### 4. Duplicate handling is a core feature

Duplicate handling is one of LinkVault’s defining capabilities.

Required long-term behavior:

- duplicate preflight on save
- duplicate checking during import / restore / sync-related flows
- exact URL match detection
- normalized URL match detection
- candidate grouping where useful
- dry-run preview before applying changes
- safe merge flow
- preserve data by default
- explicit optional removal only after review
- never delete blindly

Preferred duplicate actions:

- keep separate
- merge safely
- archive duplicate
- explicitly remove duplicate after review

When merging, important metadata must not be silently lost:
- favorite state
- tags
- lists / collections
- notes
- titles / metadata
- source and timing context where relevant

### 5. Sync and migration matter

Import/export and sync are not optional extras.
They are core product capabilities.

This includes:

- browser import
- extension-assisted workflows
- restore/import conflict handling
- future sync-oriented flows
- metadata preservation where feasible

---

## Reference benchmarks

Use these tools as directional references:

| Tool | Role for LinkVault |
|---|---|
| Karakeep | Primary functional benchmark: organization, lists, rules, feature depth |
| Linkwarden | Structured collections / sharing / dashboard benchmark |
| linkding | Minimalism / speed / search-first benchmark |
| LinkAce | Classic bookmark-management and visibility reference |
| Readeck | Lightweight operation and migration reference, but not product identity |
| Shiori | Lightweight bookmark-manager reference |

### Important benchmark rule

Borrow strengths, not identity drift.

Do **not** turn LinkVault into:
- Wallabag
- Omnivore
- Pocket-style reader products
- archive-first reading systems

---

## Current status

LinkVault is in active development.

The project already includes substantial work in these areas:

### Bookmark core
- saving links
- URL normalization
- metadata fetching
- favorites
- pinned state
- tags
- collections
- notes
- full-text search via SQLite FTS5
- filters for favorite / pinned / domain / tag / collection / status / text
- bulk actions

### Duplicate handling
- duplicate detection
- duplicate preflight
- dedup dry-run
- merge without hard delete
- loser bookmark preserved by default
- conflict-oriented review flows for restore/import-related scenarios

### Views / UI building blocks
- bookmark list
- inline editing
- compact / detailed / grid-style views
- saved views
- starter views
- active-view chips

### Auth / admin
- admin and user roles
- user-bound tokens
- password change
- admin password reset
- admin management UI

### Proxmox / infrastructure
- Proxmox LXC installer
- backup / restore / update scripts
- helper CLI
- real smoke-tested deployment path

### Extension
- Firefox companion extension
- server-backed restore preview sessions
- per-item conflict decisions

---

## Product direction correction

A previous framing described LinkVault too strongly as a “bookmark and archiving platform.”
That wording is no longer the correct steering frame.

### Correct frame
LinkVault is a **bookmark/favorites/link-management and sync platform**.

### Archive-related functionality
Archive-related behavior may still exist, but must be treated as:
- secondary
- supportive
- optional
- never dominant over bookmark workflows

### Conflict center
The Conflict Center is useful, but it must support the bookmark product.
It must not become the product identity.

---

## What matters most now

At this stage, LinkVault should prioritize:

1. bookmark-management-first navigation
2. favorites / tags / lists / collections workflows
3. quick-add and inbox triage
4. duplicate review / merge / safe-remove UX
5. strong import / export / migration coverage
6. sync-aware workflows that help bookmark management
7. Proxmox polish after core product gaps are addressed

### Lower priority than the above
- archive-first expansion
- reader-first UX
- content-consumption features
- enterprise provisioning
- broad team features
- visual polish detached from workflow quality

---

## Architecture and design decisions

### Explicit decisions
- self-hosted only
- no cloud path
- stdlib-only Python core
- SQLite only
- FTS5 for full-text search
- AGPL-3.0
- no hard delete on dedup by default
- duplicate preflight before unsafe merge behavior
- Proxmox LXC as primary deployment target
- backup/restore must be testable before community-scripts submission
- German primary working language, bilingual repository docs
- admin manages users
- no self-service registration in current phase

### Important interpretation rule
Older implementation decisions remain historically valid, but must now be interpreted through the bookmark-management-first mission.

For example:
- conflict resolution remains useful
- restore sessions remain useful
- admin/profile work remains useful

But these must support the core bookmark product rather than replace its focus.

### Inferred structural decisions
- `auth.py` remains a separate module
- settings remain stored in a generic `user_settings` table
- restore/conflict logic remains server-side
- roadmap and status docs remain living documents
- research docs should be written into repo files, not left only in chat

---

## Open tasks / unresolved questions

### Highest-value product gaps
- stronger bookmark-management navigation
- stronger favorites workflow
- stronger tags / lists / collections clarity
- stronger quick-add experience
- stronger duplicate review UX
- stronger bulk cleanup flows
- broader browser/tool import coverage
- explicit UI / GUI architecture blueprint for bookmark management

### In progress / status-sensitive
- scoped settings per user
- profile page / admin entry refinement
- import/migration broadening
- sync-related conflict behavior

### Planned but non-primary
- team / shared collections
- SCIM / IdP provisioning
- Go migration
- archive-heavy features
- reader-centric features

---

## UI / UX / GUI guidance

LinkVault must be evaluated across four separate concerns:

- UX = workflows and overall usage experience
- UI = visual design system and information hierarchy
- GUI = concrete interactive components and layout structures
- usability = efficiency, operability, clarity

These must not be collapsed into one vague “UX” bucket.

### Interface direction
The interface should feel closer to:
- Karakeep
- Linkwarden
- linkding

than to a read-later reader product.

### Required interface priorities
- clear navigation
- clear bookmark list or card views
- visible favorites handling
- visible filters and search
- visible lists / collections / tags
- low-friction quick-add
- visible duplicate review entry point
- practical bulk operations
- clear settings / profile / admin separation

### Important note
UI/GUI quality for bookmark workflows is not “mere polish.”
Navigation, layout, list management, filter visibility and duplicate interaction quality are core product quality.

---

## Known strategic risks

### 1. Archive drift
Risk: LinkVault drifts toward archive / reader / content-consumption identity.

Countermeasure:
Always ask whether a change improves bookmark management first.

### 2. Conflict-center overgrowth
Risk: conflict and restore systems become more central than everyday bookmark use.

Countermeasure:
Keep bookmark save, organize, favorite, search, filter and dedup workflows primary.

### 3. UI deprioritization drift
Risk: “UI polish later” turns into weak navigation and poor operability.

Countermeasure:
Treat bookmark workflow clarity as core functionality, not optional polish.

### 4. Import engine under-prioritization
Risk: browser/tool import remains “researched only” for too long.

Countermeasure:
Keep migration fidelity and metadata preservation as explicit roadmap goals.

---

## Files that matter most

### Steering / planning
- `CLAUDE.md`
- `docs/ROADMAP.md`
- `docs/linkvault_statusanalyse.md`

### Core backend
- `src/linkvault/server.py`
- `src/linkvault/store.py`
- `src/linkvault/auth.py`
- `src/linkvault/metadata.py`

### Extension
- `extensions/linkvault-companion/popup.js`
- `extensions/linkvault-companion/shared.js`

### Validation
- `tests/test_store.py`
- `tests/test_auth.py`
- `tests/test_server_html.py`
- `tests/test_extension_assets.py`

---

## Workflow preferences

- start each session with roadmap and status check
- be critical, not defensive
- do not preserve wrong product direction out of inertia
- keep commits small and atomic
- keep docs updated with product-impacting changes
- prefer complete and correct foundations over shortcuts
- keep self-hosted Proxmox compatibility in scope
- preserve safe dedup behavior by default

---

## Privacy / safe handling

- never include credentials, tokens, passwords, private hostnames, personal paths, CTIDs, account names
- replace with placeholders:
  - `<USER>`
  - `<PRIVATE_PATH>`
  - `<SECRET>`
  - `<TOKEN>`
  - `<EMAIL>`

- do not upload raw oversized session logs without chunking / sanitization
- research files should be attached safely, not stored in unsafe persistent memory paths

---

## Final steering rule

When unsure between two directions, prefer the one that makes LinkVault a better:

- bookmark manager
- favorites manager
- link organizer
- duplicate cleanup tool
- sync-capable self-hosted platform

Do not prefer the direction that mainly improves LinkVault as a reader or archive-first product.
``` id="vj8ra0"

Wenn du es sauber machen willst, würde ich:

- die aktuelle `PROJECT_MEMORY.md` in `PROJECT_MEMORY.backup-2026-04-28.md` umbenennen
- dann diese neue Fassung als `PROJECT_MEMORY.md` speichern

So bleibt der alte Verlauf erhalten, aber Claude bekommt eine klare neue Steuerung.

Wenn du magst, mache ich dir als Nächstes noch eine **kurze Diff-Liste**, also nur die Abschnitte, die du in `PROJECT_MEMORY.md` konkret austauschen musst, statt die ganze Datei neu zu schreiben.

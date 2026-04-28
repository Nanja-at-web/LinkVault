# ROADMAP.en.md

## LinkVault Roadmap

**Status:** 2026-04-28  
**Project:** LinkVault  
**Direction:** self-hosted bookmark, favorites, link-management, dedup and sync platform

---

## 0. Product mission

LinkVault is primarily a:

- bookmark manager
- favorites manager
- link organization system
- duplicate cleanup tool
- import/export- and sync-capable self-hosted product

### Primary goals
LinkVault should be especially good at:

- saving links quickly
- managing large bookmark libraries
- maintaining favorites
- organizing tags, lists and collections
- search, filters and sorting
- bulk actions
- detecting, reviewing, merging and optionally removing duplicates
- loss-aware import and export
- controlled sync-adjacent workflows
- lightweight operation on Proxmox VE / Debian LXC

### Not the primary mission
LinkVault is **not primarily**:

- a read-later product
- a reader app
- a web archive as the main product
- a knowledge base
- a note-taking tool with bookmark side functionality

Reader, archive or AI features may be added later as optional extensions, but they must **not** dominate this roadmap.

---

## 1. Roadmap principles

### 1.1 Bookmark first
Anything that clearly improves everyday bookmark management comes first.

### 1.2 Safe by default
Import, dedup, merge, restore and sync-adjacent flows must be safe, reviewable and understandable.

### 1.3 UI/GUI is not secondary
Navigation, search/filter clarity, favorites handling, bulk actions and duplicate UX are core quality, not mere polish.

### 1.4 Self-hosting reality matters
The default path stays lightweight, robust and LXC-friendly.

### 1.5 Heavy features stay optional
Archive workers, reader extracts, screenshots/PDF, AI or heavy platform services remain optional later extensions.

---

## 2. Current strategic assessment

### Already strong
- core bookmark logic
- URL normalization
- metadata foundation
- favorites / tags / collections / saved views
- duplicate preflight
- dedup dry-run / merge direction / safe merge philosophy
- import / preview thinking
- companion / browser proximity
- Proxmox / LXC operation
- backup / restore / update

### Biggest visible gaps
- bookmark-centered main navigation
- clear main working surface
- quick-add everyday flow
- strong favorites / lists / collections / tags UX
- visible Duplicate Center
- broader import / export / migration paths
- consistent GUI architecture

---

## 3. Priority order

The roadmap follows this order:

1. **Bookmark workspace UI**
2. **Quick Add + Inbox + Favorites + Organization**
3. **Duplicate Center + safe duplicate maintenance**
4. **Import / Export / Migration**
5. **Sync-adjacent conflict and re-import flows**
6. **Operational maturity / Proxmox / community-scripts**
7. **Optional extensions**
8. **Archive / reader / AI topics only later**

---

## 4. Phases

---

## Phase 0 — Foundation and operations
**Goal:** Keep LinkVault reliably installable, maintainable and testable.

### Target state
- stable Python / SQLite core
- clean Debian / LXC operation
- reliable backup / restore / update paths
- testable operational tooling
- clear development environment

### Included
- installation path
- systemd operation
- data paths
- backup / restore
- update
- helper
- requirements check
- Proxmox / LXC smoke tests
- Windows / development docs

### Done when
- fresh installation runs reproducibly
- healthcheck is stable
- backup / restore is testable and understandable
- update path is not fragile

### Lower priority in this phase
- cosmetic admin extensions
- heavy platform services
- archive workers

---

## Phase 1 — Bookmark core
**Goal:** LinkVault becomes clearly usable as a bookmark and favorites manager.

### Core functions
- save bookmarks
- fetch metadata
- inbox
- favorites
- pins
- tags
- lists / collections
- search
- filters
- sorting
- saved views
- bulk actions
- inline / detail editing

### Important UX/GUI goals
- clear sidebar or equivalent primary navigation
- areas for:
  - Inbox
  - All Bookmarks
  - Favourites
  - Lists / Collections
  - Tags
  - Duplicates
  - Import / Export
  - Archive
  - Settings / Profile / Admin
- fast bookmark list
- visible filters
- visible favorites handling
- usable Compact / Detailed / Grid views

### High priority in Phase 1
- Quick Add modal
- inbox default
- favorites view
- bulk favorite / bulk tags / bulk collections
- saved sorting / default view
- clear list / collection / tag operability

### Done when
- LinkVault feels like a real bookmark workspace in daily use
- new links can be captured quickly and without friction
- favorites and organization are visible and easy to use

---

## Phase 2 — Duplicate detection and cleanup
**Goal:** LinkVault becomes an unusually strong tool for safe duplicate maintenance.

### Core functions
- duplicate preflight on save
- exact URL detection
- normalized URL detection
- similar candidates
- dry-run
- merge plan
- winner suggestion
- field comparison
- undo / history direction
- merge without blind deletion
- marked losers instead of immediate data destruction

### Duplicate Center
A dedicated surface for:
- duplicate groups
- sorting by score / risk
- bulk modes:
  - safe
  - review
  - similar
- visibility of:
  - tags
  - collections
  - favorite state
  - notes
  - import origin
  - metadata differences

### Important next steps
- finish Duplicate Center UI
- add Safe Remove as an explicit action
- improve merge history
- add maintenance score
- integrate dead favorites / broken links into maintenance flows

### Do not do
- no hard automatic deletion in the standard flow
- no silent overwrites

### Done when
- duplicate cleanup is not only technically strong but also clear and safe in the UI
- users can clean up large libraries in a controlled way

---

## Phase 3 — Import / Export / Migration
**Goal:** LinkVault becomes a strong destination system for browser and tool migrations.

### Import targets
- HTML as baseline
- Chromium JSON
- Firefox JSON / JSONLZ4
- Safari ZIP
- later additional tool importers

### Import principles
- preview before commit
- duplicate checks before import
- conflict visibility
- raw data retention
- visible origin:
  - browser
  - profile
  - file
  - path
  - timestamps
  - import session

### Export targets
- general bookmark export
- filtered export
- browser-friendly structures
- stable re-import basis

### High priority
- keep HTML import robust
- expand vendor enrichment step by step
- generic CSV / JSON import
- later add tool importers selectively

### Done when
- import is not just “data in” but a clean migration workflow
- users can understand what was imported, merged or skipped

---

## Phase 4 — Companion extension and sync-adjacent flows
**Goal:** Browser and LinkVault work together in a controlled way.

### Companion goals
- save current tab
- read browser bookmarks
- send import preview
- browser re-import with preview
- duplicate preflight in extension flows
- structured conflict visibility

### Sync-adjacent principles
- no blind two-way sync
- no automatic deletion
- no silent overwrites
- conflicts remain visible
- decisions are understandable
- import is not automatically backup
- restore is not automatically sync

### Important next steps
- strengthen duplicate / conflict UX in the extension
- keep filtered export clean
- improve drift / snapshot logic where it has bookmark value
- preserve browser metadata carefully

### Do not do
- no “magic” background sync without preview
- no reader / archive logic inside the extension

### Done when
- the extension clearly complements LinkVault as a bookmark / import / export / dedup tool

---

## Phase 5 — Profile, admin and small multi-user foundations
**Goal:** Solid small multi-user base without product drift.

### Included
- admin / user roles
- user-scoped settings
- profile area
- admin area
- API token management
- password change / reset
- clean separation of:
  - personal area
  - admin
  - operations

### Important
This phase stays subordinate to the bookmark core.

### Not the main focus
- large team / org functions
- SCIM / IdP
- global enterprise provisioning

### Possible later
- shared collections
- viewer / editor models per list / collection

---

## Phase 6 — Proxmox / community-scripts maturity
**Goal:** LinkVault becomes a convincing self-hosted product on Proxmox.

### Goals
- stable one-liner
- reproducible LXC tests
- documented update / backup / restore path
- helper meaningfully expanded
- community-scripts-compatible maturity

### Important steps
- consolidate installer and helper scripts
- keep requirements checks clear
- improve logs and failure signals
- stabilize helper features
- prepare submission maturity

### Do not over-prioritize
If UI/GUI, dedup or import still have major gaps, product core comes before submission formalities.

---

## Phase 7 — Automation and rules
**Goal:** LinkVault organizes large libraries smarter without overloading the core.

### Possible contents
- domain rules
- path rules
- text / keyword rules
- automatic tag / list / collection suggestions
- favorite / priority suggestions
- smart collections
- activity / maintenance hints

### Principle
Automation should improve bookmark maintenance, not turn the product into an AI / reader / archive machine.

---

## Phase 8 — Optional later extensions
**Goal:** Additional depth without burdening the core.

### Only optional and lower priority
- reader extracts
- screenshot / PDF / single-HTML
- AI summaries
- archive worker
- heavy platform services
- alternative release artifacts
- deeper sharing / team extensions

### Condition
These topics only come after:
- the bookmark core is strong
- the GUI is solid
- Duplicate Center works well
- import / sync / migration are stable
- self-hosted operation does not suffer

---

## 5. Current concrete to-do order

### Do first now
1. finish bookmark-centered navigation
2. strengthen the main bookmark view
3. finish Quick Add + Inbox flow
4. strengthen favorites / tags / lists / collections UX
5. prioritize Duplicate Center UI

### Then
6. broaden import / export / migration paths
7. consolidate companion / browser flows
8. improve sync-adjacent conflict flows
9. complete admin / profile cleanly
10. increase Proxmox / community-scripts maturity

### Later
11. rules / smart collections
12. optional archive / reader / AI extensions

---

## 6. What is intentionally not prioritized right now

These items are intentionally **not** at the top of the roadmap:

- reader mode
- web archiving as a main feature
- screenshot / PDF / single-HTML as standard path
- WARC
- AI-first product logic
- large team / org functions
- enterprise provisioning
- platform / multi-service expansion
- design flourishes without bookmark value

---

## 7. Success criteria

The roadmap is on track when LinkVault is clearly recognizable as:

- a very good bookmark manager
- a strong favorites tool
- a clean link organizer
- a safe duplicate cleanup system
- a reliable import / export / sync-capable self-hosted system

Not:
- a half-finished reader
- an archive system with bookmark side functionality
- a UI-heavy dashboard without a strong working surface

---

## 8. Decision rule for new tasks

For every new feature, UI change and architecture idea, ask:

**Does this clearly improve LinkVault as a bookmark, favorites, organization, dedup, import/export and sync platform?**

If the answer mainly is:
- “it makes LinkVault more of a reader app”
- “it makes LinkVault more archive-heavy”
- “it makes LinkVault heavier instead of more useful”

then the priority is currently wrong.

# Roadmap Solutions

**Status:** 2026-04-28

This document translates the roadmap into concrete implementation direction.

It is intentionally more practical than aspirational:
- what blocks Version 1
- what should be solved first
- what can stay lightweight
- what should remain optional later

---

## 0. Guiding decision

LinkVault remains **small, bookmark-first and LXC-friendly by default**.

### Core path
The default product path stays focused on:
- bookmark management
- favorites
- tags / lists / collections
- search / filters / sorting
- duplicate review and cleanup
- import / export / migration
- sync-adjacent but controlled browser flows
- Proxmox / Debian LXC operation

### Optional later paths
These may exist later, but do not steer the core:
- archive workers
- reader extracts
- screenshot / PDF / single-HTML
- AI-heavy helpers
- heavier platform services
- large team / org features

### Core rule
Before adding large new capabilities, stabilize:
- UI / navigation
- duplicate workflows
- import / migration
- safe browser round-trips
- operations / backup / restore / update

---

## 1. Current highest priorities

## Priority 1 — Bookmark workspace UI and navigation

The core logic is already ahead of the visible product surface.

The next major step is to make LinkVault clearly recognizable as a bookmark and favorites manager in the UI.

### Needed outcomes
- clear primary navigation
- visible areas for:
  - Inbox
  - All Bookmarks
  - Favourites
  - Lists / Collections
  - Tags
  - Duplicates
  - Import / Export
  - Profile / Settings / Admin
  - Operations
- stronger main bookmark working view
- clearer filters / sort / bulk action placement
- visible favorites handling
- visible duplicate entry point

### Why now
This is the biggest visible product gap.
Without it, existing strengths remain hidden.

---

## Priority 2 — Quick Add and everyday capture

The bookmark core already exists, but the everyday capture flow must become lighter and faster.

### Needed outcomes
- short default dialog
- URL-first flow
- Inbox as default destination
- optional expanded fields
- immediate duplicate preflight
- optional favorites / tags / list assignment

### Why now
Quick capture is one of the fastest ways to make LinkVault feel like a real daily-use bookmark product.

---

## Priority 3 — Favorites, lists, collections and tags as real working surfaces

It is not enough that these exist in the data model.
They must feel operational in daily use.

### Needed outcomes
- dedicated Favorites view
- clear lists / collections navigation
- strong tags workflow
- bulk assignment / bulk cleanup
- per-user saved views for recurring work patterns
- visible distinction between:
  - tags
  - lists
  - collections
  - favorites
  - archive

### Why now
Organization is one of LinkVault’s core promises.
It must become visible and efficient.

---

## Priority 4 — Duplicate Center UX

Duplicate handling is already one of LinkVault’s strongest differentiators.
The next step is making that strength clearly usable in the interface.

### Needed outcomes
- dedicated Duplicate Center
- candidate grouping
- winner suggestion
- field comparison
- dry-run visualization
- safe merge flow
- explicit safe-remove path
- merge history / undo visibility
- bulk cleanup modes:
  - safe
  - review
  - similar

### Why now
This is a real differentiation opportunity, not a side feature.

---

## Priority 5 — Import / export / migration breadth

Import already has the right direction.
Now it needs broader and cleaner execution.

### Needed outcomes
- keep HTML import robust
- improve preview and conflict clarity
- broaden vendor enrichment:
  - Chromium JSON
  - Firefox JSON / JSONLZ4
  - Safari ZIP
- add generic CSV / JSON import
- preserve provenance and raw vendor fields
- prepare later tool-specific importers

### Why now
Migration quality is part of LinkVault’s value proposition.
Import is data maintenance, not mere file ingestion.

---

## Priority 6 — Sync-adjacent conflict and restore logic

Conflict and restore flows remain important, but they should serve bookmark management, not dominate the roadmap.

### Needed outcomes
- keep restore / conflict logic safe and reviewable
- improve browser round-trip visibility
- make sync-adjacent decisions understandable
- keep per-item / per-group decisions where needed
- connect conflict handling to import, duplicates and migration

### Important limitation
Do not let Conflict Center become the product identity.

### Why after the above
A strong bookmark workspace and Duplicate Center create clearer product value first.

---

## Priority 7 — Proxmox and community-scripts maturity

Self-hosting quality remains a real advantage, but the core product must stay ahead of packaging polish.

### Needed outcomes
- stable installer / helper path
- clear post-install output
- reproducible LXC tests
- update / backup / restore maturity
- community-scripts-compatible conventions later

### Why here
The Proxmox path matters, but product-core clarity should come first.

---

## 2. Phase-by-phase implementation guidance

---

## Phase 0 — Foundation

### Open items
| Open item | Solution direction | Priority |
|---|---|---|
| Final backend stack decision | Keep Python through Version 1. Reconsider only if the core becomes operationally blocked. | low |
| Schema migrations | Introduce a small `schema_migrations(version, applied_at)` table and idempotent migrations. | high |
| Docker Compose for local dev | Development-only convenience, not part of the LXC runtime story. | medium |
| Node.js for extension checks | Dev/CI only. Never make Node a required LinkVault LXC runtime dependency. | medium |

### Phase rule
Do not reopen architectural debates unless they clearly unblock the bookmark core.

---

## Phase 1 — Bookmark core

### Open items
| Open item | Solution direction | Priority |
|---|---|---|
| Bookmark-centered navigation | Build clear entry points for bookmarks, favorites, tags, collections, duplicates, import/export, settings and operations. | very high |
| Quick Add | Short dialog with Inbox default, optional expanded fields, immediate duplicate preflight. | very high |
| Favorites workflow | Dedicated favorites page, quick toggle, bulk favorite handling, saved favorite views. | very high |
| Lists / collections / tags UX | Strengthen assignment, navigation and bulk operations. | high |
| Sorting defaults | Store sorting together with views/filters so users can preserve their working mode. | high |
| Display options per user | Keep user-specific display settings, but prioritize work-oriented bookmark views over archive/preview views. | medium |
| Profile and personal settings | Conservative expansion only: user profile, own tokens, password flow, personal display/companion settings. | medium |

### Phase rule
Phase 1 must make LinkVault clearly usable as a bookmark product before deeper secondary systems expand.

---

## Phase 2 — Deduplication and favorites cleanup

### Open items
| Open item | Solution direction | Priority |
|---|---|---|
| Duplicate Center UI | Strong dedicated UI for groups, comparisons, preview and action flow. | very high |
| Undo for merge | Keep or expand snapshot-based undo for safe recovery. | very high |
| Dead favorites / broken links | Lightweight health checks, initially manual or low-frequency. | medium |
| Collection or maintenance score | Build from existing signals: missing metadata, duplicates, uncategorized items, dead links. | medium |
| Safe remove | Explicit removal path after review, never as silent default. | medium |

### Phase rule
Dedup must remain safe-by-default and explainable.

---

## Phase 3 — Import / export / migration

### Open items
| Open item | Solution direction | Priority |
|---|---|---|
| Generic CSV/JSON import | Simple mapping-based migration profile for common bookmark fields. | high |
| Raw vendor payload preservation | Keep vendor-specific fields in import records, not in a fragile bookmark core schema. | high |
| Firefox JSONLZ4 | Optional parser path, but avoid making LXC runtime heavy by default. | medium |
| Safari Reading List handling | Add as an explicit import semantic if detection is reliable. | medium |
| Tool-specific importers | Add after generic import/session/provenance model is solid. | medium |

### Phase rule
Preview, provenance and duplicate checks matter more than importer count.

---

## Phase 4 — Companion extension and sync-adjacent flows

### Open items
| Open item | Solution direction | Priority |
|---|---|---|
| Duplicate UX in extension | Surface preflight and conflict choices more clearly. | high |
| API token usability | Add clearer token status and connection test flows. | medium |
| History enrichment | Optional only, with explicit permission and clear privacy boundary. | low |
| Destructive browser sync | Only after strong conflict review, undo and logging exist. | low |
| Browser sync bridges | Evaluate later, after import/export and conflict handling are mature. | low |
| Packaging and release path | Improve only after daily-use extension flows are stable. | medium |

### Phase rule
The extension must remain a bookmark/import/export companion, not a separate product identity.

---

## Phase 5 — Operations and Proxmox maturity

### Open items
| Open item | Solution direction | Priority |
|---|---|---|
| Release installer behavior | Support Git ref/tag selection, keep healthcheck and rollback awareness. | high |
| Post-install UX | Print URL, setup token, healthcheck, logs, backup, restore and update guidance clearly. | high |
| community-scripts conventions | Align gradually with `build.func` / `install.func`, but only after product-core gaps are reduced. | medium |
| ProxmoxVE-Local compatibility | Validate once script structure is more mature. | medium |
| Version matrix | Document tested Proxmox versions over time. | medium |
| Optional archive-worker profile | Document only later as a separate heavier profile. | low |

### Phase rule
Proxmox quality supports credibility, but should not hide UI/product gaps.

---

## Phase 6 — Optional later extensions

### Only after core stability
| Later topic | Direction | Priority |
|---|---|---|
| Rule engine | Start small: domain/path/text rules, no AI dependency required. | medium later |
| Smart collections | Saved searches / filtered views first, no heavy new model needed. | medium later |
| Expanded public API | After core workflows stabilize. | medium later |
| Webhooks | After activity log and API maturity. | low later |
| Archive-heavy features | Reader text, screenshot/PDF/single-HTML only after core product is strong. | low later |
| AI tagging / summaries | Optional helper only, never product identity. | low later |
| Heavy service expansion | Only if clearly needed by real usage, not by ambition alone. | low later |

---

## 3. Recommended next sprint

## Sprint focus 1 — Bookmark workspace UI
Result:
- clear navigation
- better bookmark working surface
- visible favorites / tags / collections / duplicates
- less “all-in-one page” feeling

### Why first
This is the biggest visible product gain.

## Sprint focus 2 — Quick Add
Result:
- URL-first quick dialog
- Inbox default
- expandable extra fields
- integrated duplicate preflight

### Why second
It improves everyday use immediately.

## Sprint focus 3 — Duplicate Center UX
Result:
- stronger visible dedup workflow
- better candidate review
- better merge confidence
- clearer cleanup path

### Why third
This is one of LinkVault’s strongest differentiation opportunities.

## Sprint focus 4 — Migration breadth
Result:
- broader import formats
- better provenance handling
- stronger preview/conflict paths

### Why fourth
Import is one of LinkVault’s core promises.

---

## 4. Explicitly later

These topics stay later on purpose:

- screenshot / PDF / single-HTML
- reader extract
- AI tagging / summaries
- destructive browser sync
- PostgreSQL / Redis / external search
- Go rewrite / migration
- official community-scripts submission before product-core clarity
- archive-heavy worker design as a default expectation

They are not forbidden.
They are simply not the best next moves.

---

## 5. Final implementation rule

For every proposed solution, ask:

**Does this solution make LinkVault clearly better as a bookmark, favorites, organization, dedup, import/export and sync-capable self-hosted product?**

If the answer is mainly:
- “it expands archive depth”
- “it improves reader behavior”
- “it makes conflict infrastructure more elaborate without stronger bookmark value”
- “it makes the stack heavier before the core becomes clearer”

then the solution is being prioritized too early.

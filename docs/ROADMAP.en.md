# MVP Roadmap

Status legend:

- `[x]` done
- `[~]` partially done
- `[ ]` open

## Phase 0: Foundation

- [x] Define repository structure.
- [x] Choose license: AGPL-3.0-or-later.
- [x] Evaluate the deep research collection and derive product priorities.
- [x] Evaluate the UX research collection and derive UX priorities.
- [x] Add English repository entry point and English roadmap.
- [~] Decide final backend stack: Python remains until phase 2; Go will be
  reconsidered later.
- [~] Add data model migrations: SQLite schema exists, migrations are still
  simple.
- [ ] Local development setup with Docker Compose.
- [x] Healthcheck, `.env` configuration, fixed service data paths, and first
  systemd unit.

## Phase 1: Bookmark Core

- [x] Login and single-user setup with initial setup token.
- [~] Create, edit, and delete links.
- [x] Edit links in the UI: title, description, tags, collections, favorite,
  pin, and notes.
- [x] Bulk actions for tags, collections, favorites, and pins.
- [x] Fetch metadata: title, description, favicon, domain.
- [~] Tags, collections, favorites, and pins.
- [x] SQLite FTS5 full-text search with filters for favorite, pin, domain,
  tag, and collection.
- [~] Browser bookmark HTML import.
- [ ] API tokens for imports, extensions, and automation.
- [ ] Rework home/navigation: inbox, favorites, duplicates, tags,
  collections, archive, activity, settings.
- [ ] Quick-add flow with a short default dialog and optional advanced fields.

## Phase 2: Deduplication And Favorites Cleanup

- [x] URL normalization.
- [x] Exact duplicate detection.
- [ ] URL check endpoint inspired by linkding and Karakeep.
- [ ] Duplicate preflight while saving: open existing item, update it, attach
  archive version, save separately, or review later.
- [~] Duplicate dashboard with winner suggestions.
- [~] Merge plan with dry-run.
- [ ] Undo for merge operations.
- [ ] Merge execution without deletion: mark losing records and move data.
- [ ] Conflict center for import, sync, and merge conflicts.
- [~] Show uncategorized favorites, duplicate favorites, and dead favorites.
- [ ] Collection health score: metadata, archive status, duplicates, dead
  links, categorization.

## Phase 3: Archiving

- [ ] Show archive status in bookmark list and detail views.
- [ ] Reader extraction and stored text content inspired by Readeck.
- [ ] Highlights and notes in the reader.
- [ ] Screenshot and PDF.
- [ ] Single-HTML.
- [ ] Evaluate EPUB/OPDS-style export or reader options.
- [ ] Archive status per link.
- [ ] Link health checks.
- [ ] Include archive assets in backup/restore and merge plans.

## Phase 4: Automation

- [ ] Rule engine.
- [~] Bulk editing: bookmark cleanup exists; archive/status bulk actions are open.
- [ ] Smart collections.
- [ ] Optional AI tagging.
- [ ] Activity/audit log for imports, bulk actions, merges, deletes, restores,
  and rules.
- [ ] Expand public REST API.
- [ ] API token management with test button and visible status.
- [ ] Webhooks.
- [ ] Evaluate sync setup for browser extension, mobile share, Floccus/WebDAV,
  and API.
- [ ] Evaluate Floccus/browser sync bridge.

## Phase 5: Proxmox Installation

- [ ] Build release binary.
- [~] Debian 13 install script: local Python MVP installer exists; release
  installer is open.
- [x] Internal Proxmox LXC test script: container smoke test succeeded on
  Proxmox.
- [~] `ct/linkvault.sh`: community-scripts-like Proxmox host one-liner tested
  successfully; official submission is open.
- [~] `install/linkvault-install.sh`: experimental container installer exists;
  final community-scripts.org conventions are open.
- [~] Clarify the Community Scripts process: new scripts go through
  ProxmoxVED first, not directly through ProxmoxVE.
- [ ] Default/advanced mode following community-scripts.org conventions.
- [ ] Post-install helper for updates, settings, logs, and basic diagnostics.
- [ ] Post-install UX inspired by community-scripts.org: clearly print URL,
  setup token, healthcheck, logs, backup, restore, and update hints.
- [ ] Update function for installed LinkVault LXCs.
- [x] Backup/restore documentation: SQLite MVP docs and scripts exist.
- [x] Test backup/restore in a real Proxmox LXC: CT 112 smoke test succeeded on
  2026-04-19.
- [~] Test on Proxmox VE 8.4/9.x: first real Proxmox run succeeded; version
  matrix is open.
- [ ] Check community-scripts.org conventions with `build.func`/`install.func`.
- [ ] Test ProxmoxVE-Local compatibility.
- [ ] Prepare ProxmoxVED submission.
- [ ] Plan later ProxmoxVE maintenance after ProxmoxVED review.

## Phase 6: Migration From Existing Tools

- [ ] Import preview with dry-run and duplicate report.
- [ ] linkding import via API/export.
- [ ] Karakeep import.
- [ ] Linkwarden import.
- [ ] LinkAce import.
- [ ] Readeck import.
- [ ] Shiori import.

## Version 1 Acceptance Criteria

- Manage 10,000 bookmarks smoothly.
- Group 1,000 duplicate candidates safely.
- No merge deletes archive data without undo.
- Browser HTML import works with tags and folders.
- Proxmox LXC default installation runs without manual cleanup.
- Community Scripts path is traceable: internal one-liner, ProxmoxVED, later
  ProxmoxVE maintenance.
- Backup and restore are documented and tested.

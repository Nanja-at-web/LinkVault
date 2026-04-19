# MVP Roadmap

Status legend:

- `[x]` done
- `[~]` partially done
- `[ ]` open

## Phase 0: Foundation

- [x] Define repository structure.
- [x] Choose license: AGPL-3.0-or-later.
- [x] Evaluate the deep research collection and derive product priorities.
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
- [ ] Edit links in the UI: title, description, tags, collections, favorite,
  pin, and notes.
- [ ] Bulk actions for tags, collections, favorites, and pins.
- [x] Fetch metadata: title, description, favicon, domain.
- [~] Tags, collections, favorites, and pins.
- [x] SQLite FTS5 full-text search with filters for favorite, pin, domain,
  tag, and collection.
- [~] Browser bookmark HTML import.
- [ ] API tokens for imports, extensions, and automation.

## Phase 2: Deduplication And Favorites Cleanup

- [x] URL normalization.
- [x] Exact duplicate detection.
- [ ] URL check endpoint inspired by linkding and Karakeep.
- [~] Duplicate dashboard with winner suggestions.
- [~] Merge plan with dry-run.
- [ ] Undo for merge operations.
- [ ] Merge execution without deletion: mark losing records and move data.
- [~] Show uncategorized favorites, duplicate favorites, and dead favorites.
- [ ] Collection health score: metadata, archive status, duplicates, dead
  links, categorization.

## Phase 3: Archiving

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
- [ ] Bulk editing.
- [ ] Smart collections.
- [ ] Optional AI tagging.
- [ ] Expand public REST API.
- [ ] Webhooks.
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
- [ ] Update function for installed LinkVault LXCs.
- [~] Backup/restore documentation: SQLite MVP docs and scripts exist; real LXC
  restore test is open.
- [ ] Test backup/restore in a real Proxmox LXC.
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

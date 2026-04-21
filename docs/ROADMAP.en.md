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
- [x] Evaluate the 2026-04-20 browser/API research and derive the import
  architecture.
- [x] Evaluate the 2026-04-20 installation/requirements research and derive
  operating profiles.
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
- [ ] Browser HTML import preview: show new links, duplicates, folder paths,
  tags/collections, and conflicts before writing.
- [ ] Store import session metadata: source, file, checksum, profile, format,
  timestamp, and result counts.
- [ ] API tokens for imports, extensions, and automation.
- [~] Rework home/navigation: tabs for save, import, bookmarks, dedup, and
  operations exist; inbox, favorites, tags, collections, archive, activity,
  and settings are still open.
- [x] Make the bookmark list more compact and move filters/bulk actions into
  collapsible work bars.
- [x] Inbox/unsorted: new links without a collection automatically land in
  `Inbox`.
- [x] Rule-based tag/collection suggestions from domain, title, description,
  and URL.
- [ ] Quick-add flow with a short default dialog and optional advanced fields.

## Phase 2: Deduplication And Favorites Cleanup

- [x] URL normalization.
- [x] Exact duplicate detection.
- [x] URL check endpoint inspired by linkding and Karakeep: `/api/bookmarks/preflight`.
- [~] Duplicate preflight while saving: open existing item, update it, or
  intentionally save separately exists; archive version comes later.
- [x] Duplicate dashboard with winner suggestions, loser list, difference view,
  and clear merge button.
- [x] Merge plan with dry-run.
- [ ] Undo for merge operations.
- [x] Merge execution without deletion: update the winner, mark losing records
  as `merged_duplicate`, and move data.
- [x] Status filter for active and merged duplicates in the API/UI.
- [x] Merge history with snapshots for winner-before, losers-before, and
  winner-after.
- [ ] Conflict center for import, sync, and merge conflicts.
- [~] Show uncategorized favorites, duplicate favorites, and dead favorites.
- [ ] Collection health score: metadata, archive status, duplicates, dead
  links, categorization.

## Phase 3: Archiving

- [ ] Show archive status in bookmark list and detail views.
- [ ] Reader extraction and stored text content inspired by Readeck.
- [ ] Optional archive-worker profile: fetch the page and store readable text,
  later screenshot/PDF.
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
- [x] Post-install helper for updates, settings, logs, and basic diagnostics:
  CT 112 test succeeded on 2026-04-19.
- [ ] Post-install UX inspired by community-scripts.org: clearly print URL,
  setup token, healthcheck, logs, backup, restore, and update hints.
- [x] Update function for installed LinkVault LXCs: CT 112 smoke test succeeded
  on 2026-04-19.
- [x] Backup/restore documentation: SQLite MVP docs and scripts exist.
- [x] Test backup/restore in a real Proxmox LXC: CT 112 smoke test succeeded on
  2026-04-19.
- [x] Migration test into a second fresh Proxmox LXC: restore from CT 112 to CT
  114 succeeded on 2026-04-19.
- [~] Test on Proxmox VE 8.4/9.x: first real Proxmox run succeeded; version
  matrix is open.
- [ ] Check community-scripts.org conventions with `build.func`/`install.func`.
- [ ] Test ProxmoxVE-Local compatibility.
- [x] Requirements check for Debian/LXC, RAM, disk, systemd, Python, venv, and
  SQLite FTS5.
- [ ] Specify the archive-worker profile with extra packages and resource
  values.
- [ ] Prepare ProxmoxVED submission.
- [ ] Plan later ProxmoxVE maintenance after ProxmoxVED review.

## Phase 6: Migration From Existing Tools

- [ ] Import preview with dry-run and duplicate report.
- [ ] Chromium JSON import as optional enrichment for HTML imports.
- [ ] Firefox JSON/JSONLZ4 import as optional enrichment for HTML imports.
- [ ] Safari ZIP import with `Bookmarks.html` and Reading List detection.
- [ ] Preserve raw browser/vendor fields through `raw_vendor_payload`.
- [ ] linkding import via API/export.
- [ ] Karakeep import.
- [ ] Linkwarden import.
- [ ] LinkAce import.
- [ ] Readeck import.
- [ ] Shiori import.
- [ ] Evaluate Wallabag/Shaarli/Omnivore/Grimoire/Betula as later import
  profiles.

## Version 1 Acceptance Criteria

- Manage 10,000 bookmarks smoothly.
- Group 1,000 duplicate candidates safely.
- No merge deletes archive data without undo.
- Browser HTML import works with tags and folders.
- Import preview prevents silent overwrites and shows duplicate/conflict
  reports.
- Proxmox LXC default installation runs without manual cleanup.
- Community Scripts path is traceable: internal one-liner, ProxmoxVED, later
  ProxmoxVE maintenance.
- Backup and restore are documented and tested.

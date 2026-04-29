# AGENTS.md

Read `CLAUDE.md` first and follow it as the main project steering document for this repository.

If `CLAUDE.md`, active product docs, older summaries, backup files, historical notes, or outdated implementation details conflict, `CLAUDE.md` and the current active product docs win.

## Non-negotiable project direction

- LinkVault is primarily a self-hosted bookmark, favorites and link-management platform.
- It must stay focused on bookmarks, favorites, organization, duplicate handling, import/export and sync-adjacent workflows.
- It must not drift into a read-later-first, reader-first or archive-first product.
- Archive, reader or AI-heavy features are optional later extensions, not the primary product identity.
- LinkVault should feel like a practical bookmark workspace, not a technical dashboard and not a content-consumption product.

## Files to read first

Before making product, UI, UX, architecture or workflow decisions, read:

- `CLAUDE.md`
- `PROJECT_MEMORY.md`
- `README.md`
- `README.de.md`
- `pyproject.toml`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/linkvault_statusanalyse.md`
- `docs/ROADMAP.md`
- `docs/ROADMAP.en.md`
- `docs/RESEARCH_IMPACT.md`
- `docs/ROADMAP_SOLUTIONS.md`
- `docs/UX_RESEARCH_IMPACT.md`
- `docs/COMPANION_EXTENSION.md`
- `docs/COMPANION_EXTENSION_UPDATE.md`

## Current product priorities

Prioritize work that strengthens LinkVault as a bookmark-first product:

- bookmark-centered navigation and information architecture
- Quick Add and everyday save flow
- favorites, tags, lists and collections as real working surfaces
- Duplicate Center UX, duplicate preflight, safe merge and cleanup flows
- import/export and migration UX
- companion/browser roundtrip clarity
- lightweight self-hosting on Proxmox / Debian LXC
- clear System / Profile / Settings / Admin separation without overpowering the bookmark workflow

## Product model to preserve

Treat these concepts as distinct and visible in the product:

- Bookmark = main object
- Favourite = personal state / prominence
- List / Collection = structural organization
- Tag = flexible label
- Duplicate = maintenance / cleanup area
- Import / Export = migration module
- System / Profile / Settings / Admin = secondary areas, not primary bookmark workspace

Do not blur these concepts unnecessarily.

## Working rules

- Treat the active Markdown files as the current product source of truth.
- Historical backup files, older summaries, archived notes and research bundles are reference only, not current steering.
- Compare the actual code and UI against the active docs before proposing larger changes.
- Prefer small, logically separated changes.
- Avoid unnecessary product drift.
- Keep wording, labels and UI structure user-facing and understandable.
- Do not introduce technical/internal terminology as primary navigation if a simpler user-facing term is better.
- Preserve the single clear primary creation flow for adding bookmarks.
- Keep secondary/system areas visible but visually subordinate to daily bookmark work.
- Run relevant tests after code changes.
- Leave the worktree clean after completing tasks.

## Code and architecture guidance

- Keep the default path lightweight and self-host friendly.
- Do not introduce heavy dependencies or architecture expansion without clear product value.
- Do not move LinkVault toward a heavy archive/reader platform by accident.
- Keep duplicate handling safe by default.
- Prefer reviewable, understandable workflows over “magic” automation.
- Do not rely on runtime `.git` access for version/build metadata if the installed environment may not contain the full repository.
- Use one central source for version/build display data.

## UI / UX guidance

When changing the frontend, favor:

- fewer equal-weight navigation items
- clearer hierarchy
- clearer naming
- stronger distinction between primary and secondary actions
- visible bookmark work areas
- visible cleanup and migration areas without letting them dominate
- calm, understandable layouts over feature clutter

Reference direction:
- Linkwarden-like clarity in information architecture
- Karakeep-like separation of favorites, organization and workflow surfaces

Do not copy these products directly.
Use them as clarity references, not as identity targets.

## Validation rule

Before finishing a task, ask:

- Does this make LinkVault better as a self-hosted bookmark, favorites, organization, duplicate-cleanup, import/export and sync-adjacent platform?
- Or does it mainly make LinkVault more like a reader, archive system, technical dashboard, or unfocused multi-tool?

If the second is true, the direction is probably wrong.

## When unsure

If documentation and code disagree:

1. trust `CLAUDE.md` and the active product docs first
2. identify the mismatch clearly
3. correct the implementation toward the active product direction
4. update docs only when needed to reflect the real intended state

# CLAUDE.md — LinkVault

> Concise operational context for Claude Code and AI coding assistants.
> Last updated: 2026-04-26
> For full project history see PROJECT_MEMORY.md and BATCH_SUMMARY_1/2/3.

---

## Project overview

**LinkVault** — self-hosted bookmark and archiving platform.
**GitHub:** github.com/Nanja-at-web/LinkVault
**Stack:** Python 3.13 · SQLite + FTS5 · stdlib-only · Firefox WebExtension companion
**License:** AGPL-3.0
**Deploy target:** Proxmox VE, Debian 12 LXC (community-scripts.org one-liner pattern)
**Primary dev language (sessions):** German

**Canonical Windows repo path:**
`<PRIVATE_PATH>\Documents\git\LinkVault\LinkVault\`
*(Note: not `Documents\LinkVault\` — Codex repeatedly confused these)*

---

## Current priorities

Check `docs/ROADMAP.md` and `docs/linkvault_statusanalyse.md` at the start of every session — these are updated with every commit.

**Last known in-progress (end of Batch 3 — may not be committed):**
- Scoped settings: Saved Views migrating from instance-global → per-user (`user_id`) scope
- Profile page UI: planned, depends on scoped settings completion
- Admin UI dedicated entry point: design started

**Do NOT implement these without explicit re-request:**
- Mini structure preview per conflict group (Vorher/Nachher-Sicht der Zielpfade)
- Team / Shared Collections
- Browser import engine (researched only — no code yet)
- SCIM / IdP provisioning
- Go migration

---

## Architecture notes

- **Backend:** Pure Python, no framework, no build step. Runs as `python -m linkvault.server`.
- **Database:** SQLite only. FTS5 for full-text search. No Postgres.
- **Auth:** `src/linkvault/auth.py` — `admin` / `user` roles, user-bound tokens, password change/reset.
- **Settings:** `user_settings` key-value table in SQLite. Saved Views scoped to `user_id` (in progress).
- **Conflict Center:** Server-side conflict groups → bulk group decisions → read-only impact preview → apply.
- **Extension:** Firefox WebExtension. Server-backed restore preview sessions. Per-item conflict decisions.
- **No hard delete on dedup** — winner keeps data, loser bookmark preserved.
- **Conflict resolution always shows impact preview before applying** — never apply blindly.
- **Future team model:** Karakeep-style shared collections per list (viewer/editor). Not a global namespace.

### Design benchmarks — do not suggest replacing

| Tool | Role |
|---|---|
| Karakeep | Primary functional benchmark (features, admin API, automation) |
| Linkwarden | Collaboration/sharing benchmark (shared collections, permissions) |
| linkding | Minimalism/search benchmark (speed, search-first, low overhead) |

---

## Key files and directories

```
src/linkvault/
  server.py       — API routes, HTML UI, all HTTP endpoints, auth integration
  store.py        — SQLite CRUD, FTS5, dedup, import, conflict groups,
                    restore sessions, named views, scoped settings
  auth.py         — roles, user-bound tokens, password change/reset
  metadata.py     — URL metadata fetcher (title/desc/favicon)
  config.py       — config loader (.env / env vars)

extensions/linkvault-companion/
  popup.js        — restore preview UI, per-item conflict decisions
  shared.js       — session lifecycle, server communication
  styles.css / manifest.json

tests/
  test_store.py         — store unit tests + conflict/preview/sessions
  test_auth.py          — auth, roles, password flows, admin actions
  test_server_html.py   — HTML/UI output tests
  test_extension_assets.py
  test_docs.py          — docs ASCII check

docs/
  ROADMAP.md / ROADMAP.en.md          — ⬅ read this first each session
  linkvault_statusanalyse.md           — ⬅ running implementation status
  ADMIN_PROFILE_SHARING_PATTERNS.md   — ⬅ consult before any admin/sharing work
  ROADMAP_SOLUTIONS.md                 — already-solved problems (do not re-solve)
  DEVELOPMENT_WINDOWS.md               — Windows-specific setup

install/linkvault-install.sh           — Proxmox one-liner installer
scripts/                               — backup / restore / update / helper / check
proxmox/                               — LXC smoke tests
```

---

## Commands to know

### Run tests

```bash
# macOS/Linux
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m py_compile src/linkvault/*.py tests/*.py
git diff --check
```

```powershell
# Windows
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest discover -s tests
$files = (Get-ChildItem src\linkvault\*.py).FullName + (Get-ChildItem tests\*.py).FullName
.\.venv\Scripts\python.exe -m py_compile $files
```

### Start server locally

```bash
PYTHONPATH=src LINKVAULT_DATA=/tmp/lv.sqlite3 LINKVAULT_PORT=3091 python3 -m linkvault.server
curl -fsS http://localhost:3091/healthz
```

### JS syntax check (Windows)

```powershell
& 'C:\Program Files\nodejs\node.exe' --check extensions\linkvault-companion\popup.js
& 'C:\Program Files\nodejs\node.exe' --check extensions\linkvault-companion\shared.js
```

### Proxmox install (one-liner)

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/install/linkvault-install.sh)"
```

### Fix Windows git lock

```powershell
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -Force }
```

---

## Testing / validation

- **Baseline:** ~50 tests. Count must not decrease.
- **Every commit requires all three:** `py_compile` → `unittest discover -s tests` → `git diff --check`
- No external test framework — stdlib `unittest` only
- Bash scripts: `bash -n <script>` before commit
- Non-ASCII docs: `LC_ALL=C rg -n "[^\x00-\x7F]"` on modified files

---

## API / integration notes

- **Key env vars:** `LINKVAULT_DATA`, `LINKVAULT_PORT`, `LINKVAULT_ADDR`, `LINKVAULT_CTID`
- **Dev ports:** 3080–3092
- **Conflict Center API:** `POST /api/restore-sessions/<id>/groups/<group_key>/decide`
- **Saved Views API:** `/api/settings/...` (server-side, user-scoped in progress)
- **No Postgres, no Redis, no external search** — SQLite only
- **Browser extension:** CORS allowlist configured in server.py for companion extension

---

## Coding conventions

- stdlib-only Python core — do not add heavy pip dependencies
- `auth.py` is separate — `server.py` imports from it, never the reverse
- Commits: small and atomic, one logical step per commit, English imperative messages
- Roadmap + status docs updated in the same commit as code changes
- Research docs go into `docs/` permanently — not just noted in chat
- Windows: `(Get-ChildItem ...).FullName` for py_compile arrays (not glob)
- Windows: `Get-Content | Select-Object -Skip N -First M` for file inspection

---

## User preferences

- **Roadmap is the source of truth** for feature order — check it before proposing anything
- **Conservative:** Complete, correct foundations over fast shortcuts
- **Selective commits:** Only files belonging to one logical step per commit
- **Deferred ideas must go into docs**, not just mentioned in chat
- **Honest evaluation:** Pros and cons stated clearly, not softened
- **UI polish is explicitly deprioritized** vs. Roadmap blockers
- **No cloud path** — self-hosted Proxmox LXC only
- **Backup-first:** Infrastructure features must be testable before community-scripts submission

---

## Open issues / next steps

| Item | Status | Notes |
|---|---|---|
| Scoped settings (per-user Saved Views) | In progress — may not be committed | Check store.py/server.py before touching settings |
| Profile page UI | Planned | Depends on scoped settings |
| Admin UI entry point | Design started | Not confirmed done |
| community-scripts PR | Not submitted | Needs polish |
| Browser import engine | Researched only | Chrome/Firefox/Edge/Safari/Brave/Opera/Vivaldi/Arc/Chromium/Samsung |
| Team / Shared Collections | Architecture only | See docs/ADMIN_PROFILE_SHARING_PATTERNS.md |
| GUI architecture blueprint | Open gap | Never finalized in research phase |
| CT114 migration test | Status unclear | From Batch 1 |
| linkvault-helper CTID env bug | Fix attempted | Verify in live LXC |
| Windows git push auth | Unconfirmed | Solved on macOS, not verified on Windows |

---

## Rules for privacy and safe handling

- Never include: credentials, tokens, API keys, passwords, personal paths, hostnames, CTIDs, account names
- Replace with: `<USER>` `<PRIVATE_PATH>` `<SECRET>` `<TOKEN>` `<EMAIL>`
- Do not upload raw Codex JSONL files — chunk first (500 lines), rename `.jsonl` → `.txt`
- Do not re-upload `erweiterte_tools_admin_sharing_mit_user_template_export_import.md` — already in repo as `docs/admin-userprofile-setup_user_template_export_import.md`
- Research files: upload as file attachments only — not via API memory or persistent storage

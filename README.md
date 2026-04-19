# LinkVault

[Deutsch](README.de.md)

LinkVault is an early self-hosted bookmark, archive, and knowledge-management
project. It aims to combine the strongest ideas from Karakeep, linkding,
Linkwarden, LinkAce, Readeck, and Shiori while focusing on the gaps that still
matter in real self-hosting: safe deduplication, favorites cleanup, structured
organization, local archiving, and simple Proxmox LXC installation.

The current focus is:

- high-quality duplicate detection with safe merge plans instead of blind
  deletes
- favorites, pins, lists, collections, tags, and later rules
- automatic sorting and categorization workflows
- local archiving for web pages, articles, PDFs, images, and notes
- one-command Proxmox LXC installation inspired by community-scripts.org
- imports from browsers and existing bookmark tools

## Documentation

- [German README](README.de.md)
- [Product vision, German](docs/PRODUCT_SPEC.md)
- [Technical architecture, German](docs/ARCHITECTURE.md)
- [Deep research impact, German](docs/RESEARCH_IMPACT.md)
- [Deduplication, sorting, and categorization, German](docs/DEDUP_SORTING_CATEGORIZATION.md)
- [Proxmox community-scripts target, German](docs/PROXMOX_COMMUNITY_SCRIPT.md)
- [Debian LXC installation test, German](docs/DEBIAN_LXC_TEST.md)
- [Backup and restore, German](docs/BACKUP_RESTORE.md)
- [MVP roadmap, German](docs/ROADMAP.md)
- [MVP roadmap, English](docs/ROADMAP.en.md)

Most detailed project notes are still German. English documentation starts with
this README and the roadmap, then expands as the implementation stabilizes.

## Local MVP Prototype

The first prototype uses only the Python standard library. It stores bookmarks
in SQLite, fetches basic metadata when saving links, normalizes URLs, provides
SQLite FTS5 full-text search with filters, and shows exact duplicate groups
with a merge dry-run.

```bash
PYTHONPATH=src python3 -m linkvault.server
```

The mini UI is then available at:

```text
http://127.0.0.1:3080
```

Configuration can be provided locally through `.env` or, in service mode,
through `/etc/linkvault/linkvault.env`:

```env
LINKVAULT_ADDR=0.0.0.0:3080
LINKVAULT_DATA_DIR=/var/lib/linkvault
```

`LINKVAULT_DATA` can also point directly to a SQLite database file. Without
configuration, the local MVP uses `data/linkvault.sqlite3`.

## Debian Service

The first Debian test installer lives in `scripts/install-debian.sh`. It
installs LinkVault into a Python virtual environment under `/opt/linkvault`,
creates the `linkvault` system user, writes `/etc/linkvault/linkvault.env`,
uses `/var/lib/linkvault` as the data directory, and enables
`deploy/linkvault.service`.

```bash
sudo ./scripts/install-debian.sh
curl http://127.0.0.1:3080/healthz
```

For internal LXC tests, use `proxmox/linkvault-lxc-test.sh`. This is not an
official community-scripts.org submission yet; it is the reproducible test path
toward that goal.

Experimental Proxmox host one-liner for a new Debian LXC:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Nanja-at-web/LinkVault/main/ct/linkvault.sh)"
```

Run this command in the Proxmox VE shell. It creates a new Debian LXC, starts
it, installs LinkVault inside the container, and prints the access URL.
The installer also prints the first setup token. Use it once in the web UI to
create the initial admin user.

The official Community Scripts path is staged: this repository keeps the
experimental installer first, new script submissions should go through
`community-scripts/ProxmoxVED`, and later maintenance can target
`community-scripts/ProxmoxVE` after the script exists there.

Backup and restore for the SQLite MVP:

```bash
sudo ./scripts/backup-linkvault.sh
sudo ./scripts/restore-linkvault.sh /var/backups/linkvault/linkvault-backup-YYYYmmdd-HHMMSS.tar.gz
```

## API Snapshot

Important endpoints:

- `GET /healthz`
- `GET /api/setup/status`
- `POST /api/setup`
- `POST /api/login`
- `POST /api/logout`
- `GET /api/me`
- `GET /api/bookmarks`
- `GET /api/bookmarks?q=query`
- `GET /api/bookmarks?q=query&favorite=true&pinned=true&domain=github.com&tag=selfhost&collection=Development`
- `POST /api/bookmarks`
- `GET /api/bookmarks/{id}`
- `PATCH /api/bookmarks/{id}`
- `DELETE /api/bookmarks/{id}`
- `POST /api/import/browser-html`
- `GET /api/dedup`
- `GET /api/dedup/dry-run`

## Product Direction

The deep research collection confirms that LinkVault should not become just
another bookmark manager. The strongest positioning is a deliberate synthesis:

- linkding as the reference for robust URL deduplication, API design, and low
  operational overhead
- Karakeep as the reference for favorites, lists, rules, AI options, and modern
  knowledge workflows
- Linkwarden as the reference for long-term archiving, collections, reader
  views, and annotations
- Readeck as the reference for lightweight local reading copies, highlights,
  and EPUB/OPDS-style reader flows
- LinkAce as the reference for mature multi-user, SSO, API, and link
  monitoring features
- Shiori/Readeck as reminders to keep operations small and self-host friendly
- community-scripts.org as the operational benchmark for Proxmox LXC
  installation, logs, health checks, updates, backup, and restore

This means the next steps are: single-user setup and login, a dedup dashboard,
real LXC backup/restore testing, and better bookmark editing workflows. Archive
workers, AI, and browser sync should come later in smaller, optional layers.

## License

LinkVault is licensed under AGPL-3.0-or-later. That fits the goal of a free
self-hosted web application where network-service improvements should flow back
to the community.

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Guiding Idea

LinkVault should not merely store links. It should actively maintain a link
collection: find duplicate favorites, group similar content, improve weak
metadata, monitor dead links, and suggest useful organization through rules,
optional AI, and user behavior.

## Research

The original research bundle was extracted into
[`selfhosted-bookmark-research`](selfhosted-bookmark-research/). It contains
comparison tables, project summaries, source lists, and initial deduplication
examples.

The additional deep research collection from 2026-04-19 was evaluated in
[Research Impact](docs/RESEARCH_IMPACT.md) and reflected in the roadmap and
product priorities.

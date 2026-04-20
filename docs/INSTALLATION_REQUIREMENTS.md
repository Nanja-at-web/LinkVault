# Installation Requirements Impact

## Quelle

Diese Auswertung basiert auf der lokalen ZIP
`installation-requirements-Analyse-Resarch.zip` vom 20.04.2026. Die Sammlung
vergleicht Installation, Hosting, Code-Architektur, Abhaengigkeiten und
Proxmox-Helferskripte fuer Karakeep, linkding, Linkwarden, LinkAce, Readeck,
Shiori, Omnivore, Betula, Grimoire, Shaarli, wallabag und relevante
Proxmox-Helper-Scripts.

## Wichtigste Ableitung

LinkVault sollte nicht versuchen, im ersten Schritt wie Karakeep, Linkwarden
oder Omnivore als grosser Multi-Service-Stack zu starten. Die Research-Daten
zeigen eine klare Trennung:

- **Leichter Kern**: linkding, Shiori, Readeck, Betula und Shaarli sind
  einfacher zu betreiben und passen besser zu einem Proxmox-LXC-MVP.
- **Schwere Archiv-/Plattformfunktionen**: Karakeep, Linkwarden und Omnivore
  brauchen Browser-/Crawler-Tools, Suchdienste, Worker, teils PostgreSQL,
  Meilisearch, Redis, Objektstorage oder mehrere Dienste.

Konsequenz fuer LinkVault: Der Standard-Installationspfad bleibt klein.
Archivierung, Screenshot/PDF, Browser-Crawler, AI und externe Suche werden
spaeter als optionale Profile/Worker geplant.

## Installationsprofile

| Profil | Ziel | Abhaengigkeiten | Status |
|---|---|---|---|
| Core MVP | Bookmarks, Login, SQLite, FTS5, Dedup, Backup/Restore, Update | Python, SQLite FTS5, systemd, curl, ca-certificates | aktueller Pfad |
| Archive Worker | Reader-Extrakt, Single-HTML, Screenshot/PDF, Assets | Browser-/Crawler-Tools, Bild-/PDF-Tools, mehr RAM/Disk | spaeter optional |
| Platform Mode | groessere Teams, externe Suche, Worker-Trennung | PostgreSQL, optional Redis, optional Search-Service | spaeter bewerten |
| Release Binary | kleine Proxmox-Installation ohne Python-Venv | Go- oder anderes Release-Artefakt | Ziel nach Python-MVP |

## Aktuelle Mindest- Und Zielwerte

Aktueller Core-MVP:

- OS: Debian 13 LXC
- CPU: 2 vCPU empfohlen
- RAM: mindestens 768 MB, empfohlen 1024 MB
- Disk: mindestens 1 GB frei fuer App/DB, empfohlen 16 GB LXC-Disk
- Dienst: systemd
- Datenbank: SQLite unter `/var/lib/linkvault/linkvault.sqlite3`
- Suche: SQLite FTS5
- Port: 3080

Spaeter mit Archiv-Worker:

- RAM: eher 2048-4096 MB
- Disk: 16 GB als untere sinnvolle Grenze, je nach Archivmenge mehr
- zusaetzliche Pakete fuer Browser/Crawler/PDF/Bilder
- optional getrennte Worker- und Archivspeicher-Pfade

## Neuer Requirements-Check

Das Repo enthaelt jetzt `scripts/check-requirements.sh`. Bei Installation wird
es als `linkvault-requirements` installiert und ist auch ueber den Helper
erreichbar:

```bash
linkvault-requirements
linkvault-helper requirements
```

Der Check prueft:

- Debian-/OS-Hinweis
- systemd
- RAM
- freien Speicher am Datenpfad
- `curl`, `ca-certificates`, optional `git`
- Python-Version
- Python-`venv`
- SQLite FTS5 ueber Python

Der Check ist bewusst auf den Core-MVP zugeschnitten. Er installiert keine
schweren Archivpakete, weil diese noch nicht Teil des Standardpfads sind.

## Was LinkVault Nicht Sofort Uebernehmen Sollte

Aus der Research-Sammlung ergeben sich klare Warnungen:

- Karakeep/Linkwarden/Omnivore zeigen, wie schnell Archiv-, AI- und
  Crawler-Funktionen zu vielen Diensten fuehren.
- Meilisearch, Chromium/Playwright, Monolith, yt-dlp, GraphicsMagick,
  Ghostscript, Redis, MinIO/S3 und PostgreSQL sind nuetzlich, aber fuer den
  aktuellen Core-MVP zu frueh als Pflicht.
- Docker Compose ist fuer viele Projekte bequem, passt aber nicht automatisch
  zum community-scripts.org-LXC-Ziel.

## Was LinkVault Uebernehmen Sollte

- Von linkding: kleiner Standardbetrieb, klare API, SQLite als einfacher
  Start, Worker erst wenn noetig.
- Von Readeck/Shiori/Betula: Ein-Binary-/kleiner-Dienst-Denke fuer spaetere
  Releases.
- Von LinkAce/wallabag: breite Installationsdokumentation und klare
  Requirements.
- Von Proxmox Helper Scripts: reale Paketliste, Healthcheck, systemd,
  Logs, Update, Backup/Restore und getrennte Services nur wenn wirklich
  notwendig.

## Naechste Konkrete Schritte

1. Requirements-Check im bestehenden CT 112 nach Update ausfuehren.
2. Installer-Ausgabe um `linkvault-requirements` sichtbar halten.
3. UI weiter nicht durch mehr Felder verbessern, sondern durch echte
   Arbeitsbereiche: Inbox, Bookmarks, Dubletten, Import, Betrieb.
4. Vor Archivarbeit ein separates `archive-worker`-Profil spezifizieren.
5. Vor Community-Scripts-Einreichung Requirements-Check, Update, Backup,
   Restore und Migrationstest als offizielle Testmatrix dokumentieren.

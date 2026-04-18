# MVP-Roadmap

Status-Legende:

- `[x]` erledigt
- `[~]` teilweise erledigt
- `[ ]` offen

## Phase 0: Fundament

- [x] Repository-Struktur festlegen.
- [x] Lizenz waehlen: AGPL-3.0-or-later.
- [~] Backend-Stack final entscheiden: Python bleibt bis Phase 2, Go wird spaeter neu bewertet.
- [~] Datenmodell als Migrationen anlegen: SQLite-Schema vorhanden, Migrationen noch simpel.
- [ ] Lokale Dev-Installation mit Docker Compose.
- [x] Healthcheck, .env-Konfiguration, feste Service-Datenpfade und erste systemd Unit.

## Phase 1: Bookmark-Kern

- [ ] Login und Single-User-Setup.
- [~] Link anlegen, bearbeiten, loeschen.
- [x] Metadaten laden: Titel, Beschreibung, Favicon, Domain.
- [~] Tags, Collections, Favoriten und Pins.
- [x] SQLite-FTS5-Volltextsuche mit Filtern fuer Favorit, Pin, Domain, Tag und Collection.
- [~] Import aus Browser-Bookmark-HTML.

## Phase 2: Dubletten und Favoritenpflege

- [x] URL-Normalisierung.
- [x] Exakte Dublettenerkennung.
- [~] Dubletten-Dashboard.
- [~] Merge-Plan mit Dry-Run.
- [ ] Undo fuer Merge.
- [~] Favoriten ohne Kategorie, doppelte Favoriten und tote Favoriten anzeigen.

## Phase 3: Archivierung

- [ ] Reader-Extrakt.
- [ ] Screenshot und PDF.
- [ ] Single-HTML.
- [ ] Archivstatus je Link.
- [ ] Link Health Checks.

## Phase 4: Automatisierung

- [ ] Regel-Engine.
- [ ] Bulk-Editing.
- [ ] Smart Collections.
- [ ] AI-Tagging optional.
- [ ] API-Keys und REST-API.
- [ ] Webhooks.

## Phase 5: Proxmox-Installation

- [ ] Release-Binary bauen.
- [~] Debian 13 Installationsskript: lokaler Python-MVP-Installer vorhanden, Release-Installer offen.
- [~] Internes Proxmox-LXC-Testskript: erster Container-Smoke-Test vorhanden, community-scripts Layout offen.
- [ ] `ct/linkvault.sh` und `install/linkvault-install.sh` fuer community-scripts.org.
- [ ] Update-Funktion.
- [~] Backup/Restore-Dokumentation: SQLite-MVP-Doku und Skripte vorhanden, LXC-Restore-Test offen.
- [~] Test auf Proxmox VE 8.4/9.x: Testprozedur vorhanden, echter Proxmox-Lauf offen.

## Phase 6: Migrationen aus bestehenden Tools

- [ ] linkding Import via API/Export.
- [ ] Linkwarden Import.
- [ ] Karakeep Import.
- [ ] LinkAce Import.
- [ ] Readeck Import.
- [ ] Shiori Import.

## Akzeptanzkriterien fuer Version 1

- 10.000 Bookmarks fluessig verwalten.
- 1.000 Dubletten-Kandidaten sicher gruppieren.
- Kein Merge loescht Archivdaten ohne Undo.
- Browser-HTML-Import funktioniert mit Tags und Ordnern.
- Proxmox-LXC Default-Installation laeuft ohne manuelle Nacharbeit.
- Backup und Restore sind dokumentiert und getestet.

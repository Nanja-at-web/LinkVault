# MVP-Roadmap

## Phase 0: Fundament

- Repository-Struktur festlegen.
- Lizenz waehlen.
- Backend-Stack final entscheiden.
- Datenmodell als Migrationen anlegen.
- Lokale Dev-Installation mit Docker Compose.
- Healthcheck und erste systemd Unit.

## Phase 1: Bookmark-Kern

- Login und Single-User-Setup.
- Link anlegen, bearbeiten, loeschen.
- Metadaten laden: Titel, Beschreibung, Favicon, Domain.
- Tags, Collections, Favoriten und Pins.
- Volltextsuche ueber Titel, URL, Beschreibung.
- Import aus Browser-Bookmark-HTML.

## Phase 2: Dubletten und Favoritenpflege

- URL-Normalisierung.
- Exakte Dublettenerkennung.
- Dubletten-Dashboard.
- Merge-Plan mit Dry-Run.
- Undo fuer Merge.
- Favoriten ohne Kategorie, doppelte Favoriten und tote Favoriten anzeigen.

## Phase 3: Archivierung

- Reader-Extrakt.
- Screenshot und PDF.
- Single-HTML.
- Archivstatus je Link.
- Link Health Checks.

## Phase 4: Automatisierung

- Regel-Engine.
- Bulk-Editing.
- Smart Collections.
- AI-Tagging optional.
- API-Keys und REST-API.
- Webhooks.

## Phase 5: Proxmox-Installation

- Release-Binary bauen.
- Debian 13 Installationsskript.
- `ct/linkvault.sh` und `install/linkvault-install.sh`.
- Update-Funktion.
- Backup/Restore-Dokumentation.
- Test auf Proxmox VE 8.4/9.x.

## Phase 6: Migrationen aus bestehenden Tools

- linkding Import via API/Export.
- Linkwarden Import.
- Karakeep Import.
- LinkAce Import.
- Readeck Import.
- Shiori Import.

## Akzeptanzkriterien fuer Version 1

- 10.000 Bookmarks fluessig verwalten.
- 1.000 Dubletten-Kandidaten sicher gruppieren.
- Kein Merge loescht Archivdaten ohne Undo.
- Browser-HTML-Import funktioniert mit Tags und Ordnern.
- Proxmox-LXC Default-Installation laeuft ohne manuelle Nacharbeit.
- Backup und Restore sind dokumentiert und getestet.

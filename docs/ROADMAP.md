# MVP-Roadmap

Status-Legende:

- `[x]` erledigt
- `[~]` teilweise erledigt
- `[ ]` offen

## Phase 0: Fundament

- [x] Repository-Struktur festlegen.
- [x] Lizenz waehlen: AGPL-3.0-or-later.
- [x] Deep-Research-Sammlung auswerten und Produktprioritaeten ableiten.
- [x] UX-Research-Sammlung auswerten und UX-Prioritaeten ableiten.
- [x] Englischsprachigen Repo-Einstieg und englische Roadmap anlegen.
- [~] Backend-Stack final entscheiden: Python bleibt bis Phase 2, Go wird spaeter neu bewertet.
- [~] Datenmodell als Migrationen anlegen: SQLite-Schema vorhanden, Migrationen noch simpel.
- [ ] Lokale Dev-Installation mit Docker Compose.
- [x] Healthcheck, .env-Konfiguration, feste Service-Datenpfade und erste systemd Unit.

## Phase 1: Bookmark-Kern

- [x] Login und Single-User-Setup mit initialem Setup-Token.
- [~] Link anlegen, bearbeiten, loeschen.
- [x] Link bearbeiten in der UI: Titel, Beschreibung, Tags, Collections, Favorit, Pin, Notizen.
- [x] Bulk-Aktionen fuer Tags, Collections, Favoriten und Pins.
- [x] Metadaten laden: Titel, Beschreibung, Favicon, Domain.
- [~] Tags, Collections, Favoriten und Pins.
- [x] SQLite-FTS5-Volltextsuche mit Filtern fuer Favorit, Pin, Domain, Tag und Collection.
- [~] Import aus Browser-Bookmark-HTML.
- [ ] API-Token fuer Import, Extension und Automatisierung.
- [ ] Startseite/Navigation ueberarbeiten: Inbox, Favoriten, Dubletten, Tags,
  Collections, Archiv, Aktivitaet, Einstellungen.
- [ ] Quick-Add-Flow mit kurzem Standarddialog und optionalen erweiterten
  Feldern.

## Phase 2: Dubletten und Favoritenpflege

- [x] URL-Normalisierung.
- [x] Exakte Dublettenerkennung.
- [ ] URL-Check-Endpunkt nach linkding/Karakeep-Vorbild.
- [ ] Duplicate-Preflight beim Speichern: vorhanden oeffnen, aktualisieren,
  Archivversion anhaengen, separat speichern oder spaeter pruefen.
- [~] Dubletten-Dashboard mit Gewinner-Vorschlag.
- [~] Merge-Plan mit Dry-Run.
- [ ] Undo fuer Merge.
- [ ] Merge-Ausfuehrung ohne Loeschen: Verlierer markieren und Daten uebernehmen.
- [ ] Conflict Center fuer Import-, Sync- und Merge-Konflikte.
- [~] Favoriten ohne Kategorie, doppelte Favoriten und tote Favoriten anzeigen.
- [ ] Pflege-Score je Sammlung: Metadaten, Archivstatus, Dubletten, tote Links, Kategorisierung.

## Phase 3: Archivierung

- [ ] Archivstatus in Bookmark-Liste und Detailansicht sichtbar machen.
- [ ] Reader-Extrakt und gespeicherter Textinhalt nach Readeck-Vorbild.
- [ ] Highlights und Notizen im Reader.
- [ ] Screenshot und PDF.
- [ ] Single-HTML.
- [ ] EPUB/OPDS-nahe Export-/Reader-Option pruefen.
- [ ] Archivstatus je Link.
- [ ] Link Health Checks.
- [ ] Archivassets in Backup/Restore und Merge-Plan aufnehmen.

## Phase 4: Automatisierung

- [ ] Regel-Engine.
- [~] Bulk-Editing: Bookmark-Pflege vorhanden, Archiv-/Status-Bulk offen.
- [ ] Smart Collections.
- [ ] AI-Tagging optional.
- [ ] Activity/Audit-Log fuer Import, Bulk, Merge, Delete, Restore und Regeln.
- [ ] Public REST-API ausbauen.
- [ ] API-Token-Verwaltung mit Test-Button und sichtbarem Status.
- [ ] Webhooks.
- [ ] Sync-Setup fuer Browser-Erweiterung, Mobile Share, Floccus/WebDAV und API pruefen.
- [ ] Floccus-/Browser-Sync-Bridge pruefen.

## Phase 5: Proxmox-Installation

- [ ] Release-Binary bauen.
- [~] Debian 13 Installationsskript: lokaler Python-MVP-Installer vorhanden, Release-Installer offen.
- [x] Internes Proxmox-LXC-Testskript: Container-Smoke-Test auf Proxmox erfolgreich.
- [~] `ct/linkvault.sh`: community-scripts-aehnlicher Proxmox-Host-Einzeiler erfolgreich getestet, offizielle Einreichung offen.
- [~] `install/linkvault-install.sh`: experimenteller Container-Installer vorhanden, finale community-scripts.org-Konventionen offen.
- [~] Community-Scripts-Prozess klaeren: neue Skripte zuerst ueber ProxmoxVED, nicht direkt ueber ProxmoxVE.
- [ ] Default-/Advanced-Mode nach community-scripts.org-Konventionen.
- [ ] Post-Install Helper fuer Update, Einstellungen, Logs und Basisdiagnose.
- [ ] Post-Install UX nach community-scripts.org-Vorbild: URL, Setup-Token,
  Healthcheck, Logs, Backup, Restore und Update klar ausgeben.
- [ ] Update-Funktion fuer installierte LinkVault-LXC.
- [~] Backup/Restore-Dokumentation: SQLite-MVP-Doku und Skripte vorhanden, echter LXC-Restore-Test offen.
- [~] Backup/Restore im echten Proxmox-LXC testen: automatisches Host-Testskript vorhanden, echter Lauf offen.
- [~] Test auf Proxmox VE 8.4/9.x: erster echter Proxmox-Lauf erfolgreich, Version-Matrix offen.
- [ ] community-scripts.org-Konventionen mit `build.func`/`install.func` pruefen.
- [ ] ProxmoxVE-Local-Kompatibilitaet pruefen.
- [ ] ProxmoxVED-Einreichung vorbereiten.
- [ ] Nach ProxmoxVED-Pruefung spaetere ProxmoxVE-Pflege planen.

## Phase 6: Migrationen aus bestehenden Tools

- [ ] Import-Vorschau mit Dry-Run und Duplikatbericht.
- [ ] linkding Import via API/Export.
- [ ] Karakeep Import.
- [ ] Linkwarden Import.
- [ ] LinkAce Import.
- [ ] Readeck Import.
- [ ] Shiori Import.

## Akzeptanzkriterien fuer Version 1

- 10.000 Bookmarks fluessig verwalten.
- 1.000 Dubletten-Kandidaten sicher gruppieren.
- Kein Merge loescht Archivdaten ohne Undo.
- Browser-HTML-Import funktioniert mit Tags und Ordnern.
- Proxmox-LXC Default-Installation laeuft ohne manuelle Nacharbeit.
- Community-Scripts-Pfad ist nachvollziehbar: interner Einzeiler, ProxmoxVED,
  spaetere ProxmoxVE-Pflege.
- Backup und Restore sind dokumentiert und getestet.

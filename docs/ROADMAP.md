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
- [x] Browser/API-Research vom 20.04.2026 auswerten und Import-Architektur
  ableiten.
- [x] Installations-/Requirements-Research vom 20.04.2026 auswerten und
  Betriebsprofile ableiten.
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
- [x] Import-Vorschau fuer Browser-HTML: neue Links, Dubletten, Ordnerpfade,
  Tags/Collections und Konflikte vor dem Schreiben anzeigen.
- [ ] Import-Session-Metadaten speichern: Quelle, Datei, Checksumme, Profil,
  Format, Zeitpunkt und Ergebniszahlen.
- [x] API-Token fuer Import, Extension und Automatisierung.
- [~] Startseite/Navigation ueberarbeiten: Tabs fuer Speichern, Import,
  Bookmarks, Dubletten und Betrieb vorhanden; Favoriten, Tags,
  Collections, Archiv, Aktivitaet und Einstellungen offen.
- [x] Bookmark-Liste kompakter machen und Filter/Bulk als einklappbare
  Arbeitsleisten auslagern.
- [x] Inbox/Unsortiert: neue Links ohne Collection landen automatisch in
  `Inbox`.
- [x] Inbox sichtbar machen: eigener Einstieg in der Navigation und
  Schnellfilter in der Bookmark-Liste.
- [x] Regelbasierte Vorschlaege fuer Tags/Collections aus Domain, Titel,
  Beschreibung und URL.
- [ ] Quick-Add-Flow mit kurzem Standarddialog und optionalen erweiterten
  Feldern.

## Phase 2: Dubletten und Favoritenpflege

- [x] URL-Normalisierung.
- [x] Exakte Dublettenerkennung.
- [x] URL-Check-Endpunkt nach linkding/Karakeep-Vorbild: `/api/bookmarks/preflight`.
- [~] Duplicate-Preflight beim Speichern: vorhanden oeffnen, aktualisieren oder
  bewusst separat speichern vorhanden; Archivversion spaeter.
- [x] Dubletten-Dashboard mit Gewinner-Vorschlag, Verlierer-Liste,
  Unterschiedsansicht und klarem Zusammenfuehren-Button.
- [x] Merge-Plan mit Dry-Run.
- [ ] Undo fuer Merge.
- [x] Merge-Ausfuehrung ohne Loeschen: Gewinner aktualisieren, Verlierer als
  `merged_duplicate` markieren und Daten uebernehmen.
- [x] Statusfilter fuer aktive und gemergte Dubletten in API/UI.
- [x] Merge-Historie mit Snapshots fuer Gewinner-vorher, Verlierer-vorher und
  Gewinner-nachher.
- [ ] Conflict Center fuer Import-, Sync- und Merge-Konflikte.
- [~] Favoriten ohne Kategorie, doppelte Favoriten und tote Favoriten anzeigen.
- [ ] Pflege-Score je Sammlung: Metadaten, Archivstatus, Dubletten, tote Links, Kategorisierung.

## Phase 3: Archivierung

- [ ] Archivstatus in Bookmark-Liste und Detailansicht sichtbar machen.
- [ ] Reader-Extrakt und gespeicherter Textinhalt nach Readeck-Vorbild.
- [ ] Optionales Archive-Worker-Profil: Seite abrufen und lesbaren Text
  speichern, spaeter Screenshot/PDF.
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
- [~] API-Token-Verwaltung mit sichtbarem Status vorhanden; Test-Button offen.
- [ ] Webhooks.
- [~] Companion-Extension: Entwickler-Preview fuer Firefox/Chromium vorhanden;
  Packaging, Ordnerauswahl und bessere Vorschau offen.
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
- [x] Post-Install Helper fuer Update, Einstellungen, Logs und Basisdiagnose: CT 112 Test am 19.04.2026 erfolgreich.
- [ ] Post-Install UX nach community-scripts.org-Vorbild: URL, Setup-Token,
  Healthcheck, Logs, Backup, Restore und Update klar ausgeben.
- [x] Update-Funktion fuer installierte LinkVault-LXC: CT 112 Smoke-Test am 19.04.2026 erfolgreich.
- [x] Backup/Restore-Dokumentation: SQLite-MVP-Doku und Skripte vorhanden.
- [x] Backup/Restore im echten Proxmox-LXC testen: CT 112 Smoke-Test am 19.04.2026 erfolgreich.
- [x] Migrationstest in zweiten frischen Proxmox-LXC: Restore von CT 112 nach CT 114 am 19.04.2026 erfolgreich.
- [~] Test auf Proxmox VE 8.4/9.x: erster echter Proxmox-Lauf erfolgreich, Version-Matrix offen.
- [ ] community-scripts.org-Konventionen mit `build.func`/`install.func` pruefen.
- [ ] ProxmoxVE-Local-Kompatibilitaet pruefen.
- [x] Requirements-Check fuer Debian/LXC, RAM, Disk, systemd, Python, venv und
  SQLite FTS5.
- [ ] Archive-Worker-Profil mit zusaetzlichen Paketen und Ressourcenwerten
  spezifizieren.
- [ ] ProxmoxVED-Einreichung vorbereiten.
- [ ] Nach ProxmoxVED-Pruefung spaetere ProxmoxVE-Pflege planen.

## Phase 6: Migrationen aus bestehenden Tools

- [ ] Import-Vorschau mit Dry-Run und Duplikatbericht.
- [x] Chromium-JSON-Import fuer Chrome, Edge, Brave, Vivaldi und Opera mit
  Vorschau, Ordnerpfaden, Dublettencheck und Import.
- [ ] Firefox-JSON/JSONLZ4-Import als optionales Enrichment zum HTML-Import.
- [ ] Safari-ZIP-Import mit `Bookmarks.html` und Reading-List-Erkennung.
- [ ] Rohdaten-Erhaltung fuer Browser-/Vendor-Felder via `raw_vendor_payload`.
- [ ] linkding Import via API/Export.
- [ ] Karakeep Import.
- [ ] Linkwarden Import.
- [ ] LinkAce Import.
- [ ] Readeck Import.
- [ ] Shiori Import.
- [ ] Wallabag/Shaarli/Omnivore/Grimoire/Betula als spaetere Importprofile
  bewerten.

## Akzeptanzkriterien fuer Version 1

- 10.000 Bookmarks fluessig verwalten.
- 1.000 Dubletten-Kandidaten sicher gruppieren.
- Kein Merge loescht Archivdaten ohne Undo.
- Browser-HTML-Import funktioniert mit Tags und Ordnern.
- Import-Vorschau verhindert stille Ueberschreibungen und zeigt
  Duplikat-/Konfliktberichte.
- Proxmox-LXC Default-Installation laeuft ohne manuelle Nacharbeit.
- Community-Scripts-Pfad ist nachvollziehbar: interner Einzeiler, ProxmoxVED,
  spaetere ProxmoxVE-Pflege.
- Backup und Restore sind dokumentiert und getestet.

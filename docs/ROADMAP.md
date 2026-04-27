# MVP-Roadmap

Status-Legende:

- `[x]` erledigt
- `[~]` teilweise erledigt
- `[ ]` offen

Siehe auch: [Roadmap-Loesungsplan](ROADMAP_SOLUTIONS.md).

## Phase 0: Fundament

- [x] Repository-Struktur festlegen.
- [x] Lizenz waehlen: AGPL-3.0-or-later.
- [x] Deep-Research-Sammlung auswerten und Produktprioritaeten ableiten.
- [x] UX-Research-Sammlung auswerten und UX-Prioritaeten ableiten.
- [x] Demo-UX-Analyse zu Linkwarden, linkding und Karakeep auswerten.
- [x] Layout-/Anzeige-UX von Karakeep, Linkwarden und linkding auswerten.
- [x] Browser/API-Research vom 20.04.2026 auswerten und Import-Architektur
  ableiten.
- [x] Installations-/Requirements-Research vom 20.04.2026 auswerten und
  Betriebsprofile ableiten.
- [x] Englischsprachigen Repo-Einstieg und englische Roadmap anlegen.
- [~] Backend-Stack final entscheiden: Python bleibt bis Phase 2, Go wird spaeter neu bewertet.
- [~] Datenmodell als Migrationen anlegen: SQLite-Schema vorhanden, Migrationen noch simpel.
- [ ] Lokale Dev-Installation mit Docker Compose.
- [ ] Node.js als lokale/CI-Dev-Abhaengigkeit fuer Companion-Extension-
  Syntaxchecks einplanen, ohne Node in die LinkVault-LXC-Runtime zu ziehen.
- [x] Healthcheck, .env-Konfiguration, feste Service-Datenpfade und erste systemd Unit.

## Phase 1: Bookmark-Kern

- [~] Login, Setup und Benutzerkonten: initiales Setup-Token, Session-Login,
  Admin/User-Rollen, eigenes Passwort aendern, Admin-Passwort-Reset,
  benutzergebundene API-Tokens, Benutzerverwaltung und dedizierter Admin-Tab
  vorhanden; feinere Rechteverwaltung offen.
- [~] Link anlegen, bearbeiten, loeschen.
- [x] Link bearbeiten in der UI: Titel, Beschreibung, Tags, Collections, Favorit, Pin, Notizen.
- [x] Bulk-Aktionen fuer Tags, Collections, Favoriten und Pins.
- [x] Metadaten laden: Titel, Beschreibung, Favicon, Domain.
- [~] Tags, Collections, Favoriten und Pins.
- [x] SQLite-FTS5-Volltextsuche mit Filtern fuer Favorit, Pin, Domain, Tag und Collection.
- [~] Import aus Browser-Bookmark-HTML.
- [x] Import-Vorschau fuer Browser-HTML: neue Links, Dubletten, Ordnerpfade,
  Tags/Collections und Konflikte vor dem Schreiben anzeigen.
- [x] Browser-Import-Metadaten fuer Companion-Import speichern:
  `source_browser`, `source_root`, `source_folder_path`, `source_position`
  und `source_bookmark_id`.
- [x] Import-Session-Metadaten speichern: Quelle, Datei, Checksumme, Profil,
  Format, Zeitpunkt und Ergebniszahlen.
- [x] API-Token fuer Import, Extension und Automatisierung.
- [x] Profile und Kontoverwaltung: eigener Profil-Tab mit Benutzerinfo,
  API-Token-Verwaltung und Passwortwechsel; Admin-Tab mit Benutzerliste,
  Benutzer anlegen, Rolle aendern, Passwort-Reset und Benutzer loeschen;
  Saved Views per Nutzer gespeichert (user_id-Scope).
- [x] LinkVault-Discovery-Endpunkt `/.well-known/linkvault` fuer Companion-
  Erkennung im lokalen Netzwerk.
- [x] Startseite/Navigation ueberarbeiten: Tabs fuer Speichern, Import,
  Bookmarks, Favoriten, Tags, Collections, Archiv (Platzhalter), Einstellungen,
  Dubletten, Betrieb, Admin (nur Admin-User) und Profil vorhanden.
- [x] Bookmark-Liste kompakter machen und Filter/Bulk als einklappbare
  Arbeitsleisten auslagern.
- [x] Inbox/Unsortiert: neue Links ohne Collection landen automatisch in
  `Inbox`.
- [x] Inbox sichtbar machen: eigener Einstieg in der Navigation und
  Schnellfilter in der Bookmark-Liste.
- [x] Regelbasierte Vorschlaege fuer Tags/Collections aus Domain, Titel,
  Beschreibung und URL.
- [x] Quick-Add-Flow mit kurzem Standarddialog und optionalen erweiterten
  Feldern.
- [x] Ansichtsumschalter fuer Bookmarks: Compact List, Detailed List und Grid.
- [~] Anzeigeoptionen je Nutzer speichern: Titel, Beschreibung, Notizen, Tags,
  Collections, Domain, Datum, Favorite/Pin und Status jetzt serverseitig pro
  LinkVault-Instanz; spaetere Archiv-/Preview-Ansichten offen.
- [x] Sortierung und Filter als Standard speichern, angelehnt an linkding:
  Filter, Suche und Sortierung (sort_by, sort_order) sind serverseitig
  gespeichert und werden in Saved Views eingeschlossen.
- [x] Grid/Card-Ansicht fuer visuelles Browsing mit aktuellen Bookmark-Daten.

## Phase 2: Dubletten und Favoritenpflege

- [x] URL-Normalisierung.
- [x] Exakte Dublettenerkennung.
- [x] URL-Check-Endpunkt nach linkding/Karakeep-Vorbild: `/api/bookmarks/preflight`.
- [~] Duplicate-Preflight beim Speichern: vorhanden oeffnen, aktualisieren oder
  bewusst separat speichern vorhanden; Archivversion spaeter.
- [x] Dubletten-Dashboard mit Gewinner-Vorschlag, Verlierer-Liste,
  Unterschiedsansicht und klarem Zusammenfuehren-Button.
- [x] Merge-Plan mit Dry-Run.
- [x] Undo fuer Merge.
- [x] Merge-Ausfuehrung ohne Loeschen: Gewinner aktualisieren, Verlierer als
  `merged_duplicate` markieren und Daten uebernehmen.
- [x] Statusfilter fuer aktive und gemergte Dubletten in API/UI.
- [x] Merge-Historie mit Snapshots fuer Gewinner-vorher, Verlierer-vorher und
  Gewinner-nachher.
- [~] Conflict Center fuer Import-, Sync- und Merge-Konflikte: Import-,
  Merge- und Companion-Restore-Konflikte vorhanden; Restore-Sessions
  mit Fortschritt und Sammelentscheidung; Drift-Erkennung mit Snapshot-
  Baseline (record_sync_snapshot, compute_sync_drift) und vier
  Kategorien (geloescht, neu, geaendert, nur-LinkVault) vorhanden;
  destruktiver Zwei-Wege-Sync und Floccus-Bridge noch offen
  (Floccus-Forschung: siehe FLOCCUS_SYNC_RESEARCH.md).
- [x] Favoriten ohne Kategorie, doppelte Favoriten und tote Favoriten anzeigen:
  Favoriten-Pflege-Drawer im Favoriten-Tab mit Bericht und Link-Check-Button;
  drei Kategorien: uncategorized (nur Inbox/keine Collection), duplicated
  (gleiche normalisierte URL), dead (Link-Check fehlgeschlagen); paralleler
  HEAD/GET-Check via ThreadPoolExecutor, Ergebnisse in link_checks-Tabelle.
- [x] Pflege-Score je Sammlung: Metadaten (40 %), Dedup (30 %), Tags (15 %),
  Links (15 %); score 0-100 pro Collection; Farb-Badge (gruen/gelb/rot) im
  Collections-Tab; Archivstatus als spaeterer Faktor vorbereitet.

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
- [~] Activity/Audit-Log fuer Import, Bulk, Merge, Delete und Browser-
  Restore vorhanden; Regeln und spaetere Sync-Aktionen noch offen.
- [ ] Anpassbares Dashboard/Betrieb-Layout nach Linkwarden-Vorbild, sobald
  Bookmark-, Import- und Dedup-Workflows stabil sind.
- [x] Erste Tastaturkuerzel fuer Suche, Speichern, Import, Bookmarks und
  Dubletten.
- [ ] Shortcut-Hilfe und A11y-Pruefung fuer Fokusreihenfolge und
  Screenreader-Statusmeldungen.
- [ ] Public REST-API ausbauen.
- [x] API-Token-Verwaltung mit Test-Button: Token-Wert gegen /api/me testen,
  Ergebnis (Nutzer/Rolle oder Fehler) inline anzeigen; Sofort-testen-Button
  nach Token-Erstellung; Testen-Link pro Token-Karte.
- [ ] Webhooks.
- [~] Companion-Extension: Entwickler-Preview fuer Firefox/Chromium mit
  Ordnerauswahl, Popup-Vorschau, gefiltertem LinkVault-Export, sicherem
  Browser-Rueckimport, Zielauswahl, Konfliktentscheidungen und Restore-
  Sessions vorhanden; Packaging, destruktiver Sync und feinere Einzel-Link-
  Auswahl offen.
- [x] Companion-Entwickler-Updatepfad dokumentiert: stabile Firefox-ID,
  Reload statt Entfernen, Token/URL bleiben beim Reload normalerweise erhalten.
- [x] Companion-Importfilter fuer Ordner, Textsuche, Adresse/Domain,
  hinzugefuegt-Datum und bereits vorhandene URLs.
- [x] Companion-Discovery: LinkVault ueber aktuelle Eingabe, gespeicherte URL,
  offene Tabs, `linkvault.local`, `linkvault` und optionalen Subnetzscan finden.
- [ ] Optionales History-Enrichment fuer zuletzt besucht und meistbesucht nur
  mit expliziter Browser-History-Berechtigung.
- [ ] Sync-Setup fuer Browser-Erweiterung, Mobile Share, Floccus/WebDAV und API pruefen.
- [x] LinkVault-Export-Endpunkt fuer Browser-Bookmark-Baum:
  `GET /api/export/browser-bookmarks` mit Query/Favorit/Pin/Domain/Tag/
  Collection/Status-Filtern.
- [x] Companion-Rueckimport in den Browser als sicherer erster Schritt:
  Vorschau, Restore in neuen Ordner oder gewaehlten bestehenden Browser-
  Ordner, sowie Skip/Merge/Update fuer doppelte Links ohne Browserdaten zu
  loeschen.
- [ ] Destruktiver Browser-Sync mit Loeschwarnung und vollstaendigem
  Konfliktlog.
- [ ] Floccus-/Browser-Sync-Bridge pruefen.
- [ ] Masonry-Ansicht und Bildoptionen Cover/Contain nach Karakeep-Vorbild,
  sobald Preview-/Archivdaten stabil sind.

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

- [~] Import-Vorschau mit Dry-Run und Duplikatbericht: Core- und
  Extension-Vorschau vorhanden, Import-Sessions und Conflict-Center-
  Anschluss teilweise umgesetzt; weitere Tool-Migrationen offen.
- [x] Chromium-JSON-Import fuer Chrome, Edge, Brave, Vivaldi und Opera mit
  Vorschau, Ordnerpfaden, Dublettencheck und Import.
- [~] Firefox-JSON/JSONLZ4-Import als optionales Enrichment zum HTML-Import:
  JSON-Parser vorhanden, JSONLZ4 offen.
- [~] Safari-ZIP-Import mit `Bookmarks.html` und Reading-List-Erkennung:
  ZIP mit `Bookmarks.html` vorhanden, Reading-List-Erkennung offen.
- [ ] CSV-/JSON-Import fuer andere Bookmark-Tools als generische
  Migrationsprofile.
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

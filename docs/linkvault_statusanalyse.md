# LinkVault - bereinigte Statusanalyse

**Stand:** 26. April 2026, aktualisiert nach Session
**Projekt:** <https://github.com/Nanja-at-web/LinkVault>

## Fragestellung

Geprueft wurde der Projektstatus von **LinkVault** anhand der Dokumentation im
Repository unter `/docs`, der sichtbaren Produktoberflaeche und der lokalen
Arbeitsbasis.

## Bereinigung der Ausgangsinformation

Die fruehere Statusanalyse war als Zwischenstand brauchbar, ist aber inzwischen
an mehreren Stellen ueberholt. Besonders die dort genannten "naechsten
Schritte" (`Import-Sessions`, `Merge-Undo`, `Saved Views`) sind inzwischen
nicht mehr offen, sondern umgesetzt. Diese Fassung fasst deshalb den
aktuelleren, konsolidierten Stand zusammen.

## Beruecksichtigte Dokumente

- `ROADMAP.md` und `ROADMAP.en.md`
- `ROADMAP_SOLUTIONS.md`
- `RESEARCH_IMPACT.md`
- `ARCHITECTURE.md`
- `PRODUCT_SPEC.md`
- `DEDUP_SORTING_CATEGORIZATION.md`
- `BACKUP_RESTORE.md`
- `DEBIAN_LXC_TEST.md`
- `PROXMOX_COMMUNITY_SCRIPT.md`
- `COMPANION_EXTENSION.md`
- `DEVELOPMENT_WINDOWS.md`

## Kernaussagen

### Dokumentation und Produktdenken sind weiterhin eine Staerke

`PRODUCT_SPEC.md`, `ARCHITECTURE.md`, `DEDUP_SORTING_CATEGORIZATION.md` und
`RESEARCH_IMPACT.md` wirken fuer ein Solo-Fruehprojekt weiterhin ungewoehnlich
reif. LinkVault ist nicht als loses Bookmark-Frontend gedacht, sondern als
bewusst kleine, selfhost-taugliche Synthese aus:

- linkding-artiger URL-Deduplizierung
- Karakeep-/Linkwarden-Ideen fuer Organisation und spaetere Automation
- Readeck-/Shiori-Naehe bei Betrieb und Leichtgewichtigkeit
- community-scripts-/Proxmox-Tauglichkeit

### Proxmox ist echtes Engineering, nicht nur eine Idee

Die Doku belegt nicht nur einen Installationswunsch, sondern einen real
geprueften Betriebsweg:

- LXC-Installation auf echter Proxmox-Hardware
- Healthcheck erfolgreich
- Backup/Restore getestet
- Update getestet
- Post-Install-Helper vorhanden
- Migration in einen frischen zweiten LXC nachgewiesen

Das ist fuer Version 1 ein echter Vertrauensfaktor.

### ROADMAP_SOLUTIONS.md bleibt der beste Planungsanker

Das Dokument ist weiterhin der reifste Plan, aber sein frueherer "naechster
Sprint" ist zum Teil bereits abgearbeitet. Fuer die aktuelle Priorisierung
muessen daher `ROADMAP.md` und der aktuelle Workspace mitgelesen werden.

### Companion Extension ist nicht mehr nur Preview, sondern ein echter Teil des Produkts

Der Stand ist weiter als in der alten Analyse beschrieben. Im Projekt vorhanden
und dokumentiert sind inzwischen:

- Firefox-/Chromium-Support
- API-Token und Discovery
- Speichern des aktuellen Tabs
- Browser-Bookmark-Lesen
- Import-Vorschau
- Importfilter fuer Ordner, Textsuche, Adresse/Domain und Datum
- gefilterter LinkVault-Export
- Browser-Rueckimport in neuen oder bestehende Ordner
- Conflict-Center-Anbindung fuer Link-, Zielordner- und Ordner-/Struktur-
  Konflikte mit ersten Konfliktgruppen und Sammelentscheidungen fuer
  Restore-Sessions

### Auth und Benutzerverwaltung sind jetzt vollstaendig als eigene Bereiche sichtbar

Im aktuellen Stand vorhanden:

- Admin/User-Rollen
- benutzergebundene API-Tokens
- eigener Passwortwechsel
- Admin-Passwort-Reset
- dedizierter **Profil-Tab**: Benutzerinfo, API-Token-Verwaltung, Passwortwechsel
- dedizierter **Admin-Tab** (nur fuer Admins sichtbar): Benutzerliste, Benutzer
  anlegen, Rolle aendern, Passwort-Reset, Benutzer loeschen
- Saved Views per Nutzer gespeichert (`user_id`-Scope in `user_settings`)
- Robustheit: Body-Limit gegen DoS, SQLite-Timeout, JSON-Fehlerbehandlung,
  SSL-Fallback-Logging

Das ist noch kein grosses Rollen- oder SSO-System, aber die Kern-Auth-Features
sind jetzt als eigenstaendige, sauber getrennte UI-Bereiche erreichbar.

### Die groesste sichtbare Luecke bleibt die Frontend-Navigation

Backend, Infrastruktur, Deduplizierung, Importlogik, Proxmox und Extension sind
in vielen Bereichen weiter als die sichtbare Hauptoberflaeche. Favoriten-,
Collections-, Tags-, Archiv- und Einstellungs-Tabs fehlen noch.

## Roadmap-Status nach Phasen

| Phase | Status | Vorhanden | Offen |
|---|---:|---|---|
| Phase 0 - Fundament | ~97 % | Struktur, Lizenz, Research-Auswertung, englischer Einstieg, systemd, Windows-Dev-Doku | Docker Compose; Node.js-Checks sauber in lokale/CI-Routine ziehen |
| Phase 1 - Bookmark-Kern | ~90 % | Login, Rollenbasis mit Admin/User, Passwortwechsel, Benutzerverwaltung, Profil-Tab, Admin-Tab, FTS5, Inbox, Saved Views per Nutzer (user_id-Scope), Grid/List/Compact, Import-Sessions, API-Token, Import-Vorschau, Sortier-/Kategorie-Vorschlaege, Favoriten-Tab, Tags-Tab, Collections-Tab, Einstellungen-Tab | Archiv-Tab; Quick-Add; Sortierung als gespeicherter Standard vollenden |
| Phase 2 - Dedup | ~75 % | URL-Normalisierung, Preflight, Dry-Run, Merge ohne Loeschen, Merge-Undo, Merge-Historie, Conflict Center teilweise | Pflege-Score; tote Favoriten; groessere Sync-/Restore-Konflikte jenseits der aktuellen Rueckimport-Vorschau |
| Phase 3 - Archivierung | ~5 % | Weiter bewusst zurueckgestellt | Reader-Extrakt, Archivstatus, Screenshot/PDF, Single-HTML |
| Phase 4 - Automatisierung | ~45 % | Activity/Audit-Log teilweise, API-Token, Companion Extension mit Discovery, Filtern, Preview, Rueckimport und Konfliktentscheidungen | Rule Engine; Smart Collections; API-Token-Testbutton; vollstaendiger Sync; History-Enrichment nur optional |
| Phase 5 - Proxmox | ~80 % | Echter LXC-Betrieb, Installations-, Backup-, Restore-, Update- und Migrationstest, Post-Install-Helper | `build.func`/`install.func`-Konventionen; Default-/Advanced-Mode; ProxmoxVED-/community-scripts-Vorbereitung |
| Phase 6 - Migrationen | ~30 % | Chromium-JSON, Firefox-JSON teilweise, Safari-ZIP teilweise, HTML-Import mit Vorschau | JSONLZ4, generischer CSV/JSON-Import, weitere Tool-Importe |

## Was jetzt laut Roadmap wirklich als naechstes sinnvoll ist

Die frueheren naechsten drei Schritte aus `ROADMAP_SOLUTIONS.md`
(`Import-Sessions`, `Merge-Undo`, `Saved Views`) sind inzwischen erledigt.
Dadurch verschiebt sich der Fokus.

### 1. Conflict Center fuer groessere Sync-/Restore-Faelle ausbauen

Die Basis fuer Import-, Merge- und Companion-Restore-Konflikte steht bereits.
Der naechste starke Kernschritt ist daher:

- groessere Browser-Sync-/Restore-Konflikte
- klarere Konfliktvorschau fuer Struktur und Zielkonflikte
- spaetere Konfliktlogik fuer echte Ruecksynchronisation, nicht nur sicheren Restore

### 2. Frontend-Navigation endlich vollstaendig machen

Favoriten-, Tags-, Collections- und Einstellungs-Tab sind jetzt vorhanden.
Verbleibend:

- Archiv-Tab
- Einstellungen-Tab ausbauen (bisher nur Platzhalter)

Die Nutzerwirkung davon ist groesser als weiterer unsichtbarer Unterbau.

### 3. Quick-Add bauen

Der Bookmark-Kern ist funktional, aber noch nicht leicht genug fuer den
Alltagseinstieg. Ein kurzer Standarddialog mit Inbox-Default ist weiterhin ein
starker Roadmap-Punkt.

### 4. Migrationen verbreitern

Nach HTML, Chromium-JSON und den ersten Firefox-/Safari-Pfaden ist jetzt der
sinnvolle naechste Migrationsblock:

- generischer CSV-/JSON-Import
- Firefox JSONLZ4
- danach einzelne Tool-Importer

### 5. ProxmoxVED/community-scripts vorbereiten, aber nicht vorziehen

Die technische Vorarbeit ist bereits stark genug, um ernst genommen zu werden.
Offizielle community-scripts-/ProxmoxVED-Konformitaet sollte trotzdem erst
nach den groesseren Produktluecken kommen.

## Empfehlung

Wenn man nur nach "Was bringt LinkVault jetzt am weitesten?" fragt, ergibt sich
aus Roadmap und Status zusammen diese Reihenfolge:

1. **Conflict Center weiter ausbauen**
2. **Frontend-Navigation fertigziehen** (Favoriten, Tags, Collections, Einstellungen)
3. **Quick-Add**
4. **Migrationen verbreitern**
5. **Proxmox/community-scripts vorbereiten**

Erledigt seit letzter Analyse: Profil-Tab, Admin-Tab, Scoped Settings
(user_id), Haertung (Body-Limit, SQLite-Timeout, JSON-Guards, SSL-Logging),
Favoriten-Tab, Tags-Tab, Collections-Tab, Einstellungen-Tab,
Migrations-Robustheit (role/user_id-Spaltenreihenfolge), cssEscape-Fix.

## Fazit

LinkVault ist inzwischen klar mehr als ein MVP auf Papier. Die Mischung aus
realem Proxmox-Betrieb, Companion-Extension, Deduplizierung mit Undo,
Import-Sessions, Saved Views und wachsendem Conflict Center zeigt ein echtes
Produktgeruest.

Der Hebel mit der schnellsten Aussenwirkung bleibt die
**Frontend-Navigation**. Der Hebel mit dem staerksten technischen Nutzen fuer
die naechste Produktreife bleibt das **Conflict Center** inklusive
Companion-Restore und spaeterem Sync/Restore.

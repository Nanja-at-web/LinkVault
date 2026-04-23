# Roadmap-Loesungsplan

Stand: 2026-04-23

Dieses Dokument uebersetzt die offenen Roadmap-Punkte in konkrete
Loesungswege. Es ist bewusst naeher an Umsetzung als an Wunschliste: Was
blockiert Version 1, was kann klein geloest werden, und was bleibt optional?

## Leitentscheidung

LinkVault bleibt im Standard klein und LXC-freundlich:

- Python-MVP, SQLite, FTS5, systemd, Backup/Restore, Update und Companion
  Extension bleiben der Core.
- Archivierung, Screenshot/PDF, AI, PostgreSQL, externe Suche und schwere
  Browser-Worker werden Profile, nicht Pflicht fuer die normale Installation.
- Vor neuen grossen Features werden Import, Dedup, Sync/Restore und Betrieb
  stabilisiert.

## Naechste Prioritaeten

1. **Import-Sessions und Audit-Log**
   Jede groessere Aktion braucht nachvollziehbare Historie: Importquelle,
   Format, Checksumme, Ergebniszahlen, Konflikte, Bulk-Aktionen, Merges,
   Restore und Extension-Sync.

2. **Conflict Center**
   Konflikte aus Import, Dedup-Merge und Browser-Restore sollen an einer
   Stelle sichtbar werden. Erst Preview, dann bewusst anwenden.

3. **Companion-Restore verfeinern**
   Einzelne Links/Folders auswaehlen, Konfliktlogik verbessern, aber weiter
   ohne Loeschungen im Browser.

4. **Saved Views**
   Sortierung, Filter und Anzeigeoptionen als Standard speichern. Das macht
   LinkVault im Alltag deutlich ruhiger und linkding-aehnlich schneller.

5. **Community-Scripts/ProxmoxVED-Vorbereitung**
   Nicht sofort offizieller PR, sondern Layout, Default/Advanced Mode,
   `build.func`/`install.func`-Kompatibilitaet und Post-Install-Ausgabe
   sauber nachziehen.

## Phase 0: Fundament

| Offen | Loesung | Prioritaet |
|---|---|---|
| Backend-Stack final entscheiden | Python bis Version 1 weiterfuehren. Go erst pruefen, wenn Core stabil und Release-Paketierung ein echtes Problem ist. | niedrig |
| Migrationen | Kleine Migrationstabelle einfuehren: `schema_migrations(version, applied_at)`. Jede neue Spalte als idempotente Migration. | hoch |
| Docker Compose Dev-Setup | Nur fuer lokale Entwicklung: App, Volume, Port 3080. Keine Pflicht fuer LXC. | mittel |
| Node.js fuer Extension-Checks | Nur Dev/CI: `node --check extensions/linkvault-companion/*.js`. Node nicht im LXC installieren. | mittel |

## Phase 1: Bookmark-Kern

| Offen | Loesung | Prioritaet |
|---|---|---|
| Import-Session-Metadaten | Tabellen `import_sessions` und `import_records`; alle Datei- und Extension-Importe erzeugen eine Session. | sehr hoch |
| Navigation: Favoriten, Tags, Collections, Archiv, Aktivitaet, Einstellungen | Zuerst Aktivitaet und Collections/Favoriten als einfache Filterseiten, spaeter vollstaendige Verwaltungsseiten. | mittel |
| Quick-Add | Kompakter Dialog: URL, Titel optional, Inbox default, Vorschlaege. Erweiterte Felder ausklappbar. | mittel |
| Anzeigeoptionen serverseitig speichern | Tabelle `user_settings(key, value_json)`. Lokale Browser-Settings bleiben Fallback. | mittel |
| Sortierung/Filter als Standard speichern | `saved_views` oder `user_settings.bookmark_default_view`; Button "Als Standard speichern". | hoch |

## Phase 2: Dubletten und Favoritenpflege

| Offen | Loesung | Prioritaet |
|---|---|---|
| Undo fuer Merge | Bestehende Merge-Snapshots reichen als Basis. API: `POST /api/dedup/merges/{id}/undo`. Gewinner/Verlierer aus Snapshot wiederherstellen. | sehr hoch |
| Conflict Center | Start mit Import- und Merge-Konflikten. Modell: `conflicts(id, kind, source_id, state, payload_json, created_at)`. | sehr hoch |
| Tote Favoriten | Link-Health-Check als leichter HEAD/GET-Job, erst manuell starten, spaeter regelmaessig. | mittel |
| Pflege-Score je Sammlung | Reiner Score aus vorhandenen Daten: fehlende Metadaten, Inbox-Anteil, Dubletten, tote Links. | mittel |

## Phase 3: Archivierung

| Offen | Loesung | Prioritaet |
|---|---|---|
| Archivstatus | Spalten/Tabelle fuer `archive_state`, `last_archived_at`, `archive_error`. Sichtbar machen, bevor Worker gebaut wird. | mittel |
| Reader-Extrakt | Optionales Worker-Profil. Zuerst nur HTML abrufen und Readability-Text speichern. | niedrig |
| Screenshot/PDF/Single-HTML | Spaeter eigenes Profil mit Playwright/Browser-Tools und hoeheren LXC-Ressourcen. | niedrig |
| Archivassets in Backup/Restore | Backup-Skripte um `/var/lib/linkvault/archive` erweitern, sobald Assets existieren. | niedrig |

## Phase 4: Automatisierung

| Offen | Loesung | Prioritaet |
|---|---|---|
| Activity/Audit-Log | Vor Regel-Engine bauen. Das ist die Grundlage fuer Vertrauen und Fehlersuche. | sehr hoch |
| Rule Engine | Klein starten: Wenn Domain/URL enthaelt X, dann Tags/Collection setzen. Keine AI noetig. | mittel |
| Smart Collections | Gespeicherte Suche plus Filter. Keine neue Datenstruktur erzwingen. | mittel |
| API-Token Test-Button | In `Betrieb` Button gegen `/api/bookmarks` oder `/healthz` mit Token anzeigen. | mittel |
| Webhooks | Erst nach Audit-Log und stabiler Public API. | niedrig |
| History-Enrichment | Optional und explizit, weil `history`-Berechtigung sehr sensibel ist. | niedrig |
| Browser-Sync mit Loeschungen | Erst nach Conflict Center, Undo und Audit-Log. Standard: kein Loeschen. | niedrig |
| Masonry/Preview-Bilder | Erst nach Archiv-/Preview-Daten. Vorher Compact/List/Grid weiter verbessern. | niedrig |

## Phase 5: Proxmox-Installation

| Offen | Loesung | Prioritaet |
|---|---|---|
| Release-Binary | Fuer Python-MVP nicht blockierend. Erst Wheel/Tagged Release, Go-Binary spaeter bewerten. | niedrig |
| Release-Installer | Installer soll Git-Ref/Tag statt nur `main` koennen. Healthcheck und Rollback behalten. | hoch |
| Default/Advanced Mode | `ct/linkvault.sh`: Default minimal fragen, Advanced fuer CTID, Storage, RAM, CPU, Bridge, IP. | hoch |
| Post-Install UX | Abschlussausgabe vereinheitlichen: URL, Setup-Token, Helper-Befehle, Backup, Restore, Update, Logs. | hoch |
| Community-Scripts-Konventionen | Separaten Kompatibilitaetsordner vorbereiten, aber erst ProxmoxVED pruefen. | mittel |
| ProxmoxVE-Local | Einzeiler und lokale Skriptstruktur testen; Dokumentation ergaenzen. | mittel |
| Version-Matrix | Tests auf Proxmox VE 8.4 und 9.x dokumentieren. | mittel |
| Archive-Worker-Profil | Ressourcenprofil definieren: mehr RAM, mehr Disk, zusaetzliche Pakete. | niedrig |

## Phase 6: Migrationen

| Offen | Loesung | Prioritaet |
|---|---|---|
| JSONLZ4 fuer Firefox | Optionales Parser-Modul, vermutlich externe LZ4-Abhaengigkeit nur fuer Dev/Core-Import. Nicht LXC-schwer machen. | mittel |
| Safari Reading List | ZIP/HTML bleibt Basis; Reading List als eigener Importtyp markieren, wenn Daten sicher erkannt werden. | niedrig |
| CSV/JSON generisch | Mapping-Import: Felder `url`, `title`, `description`, `tags`, `collections`, `notes`. | hoch |
| `raw_vendor_payload` | Import-Records speichern Rohdaten, nicht direkt Bookmark-Tabelle ueberladen. | hoch |
| linkding Import | Zuerst Datei-/API-Profil mit URL, Titel, Beschreibung, Tags, unread/shared falls vorhanden. | mittel |
| Karakeep/Linkwarden/Readeck/Shiori/LinkAce | Nach generischem JSON/CSV und Import-Sessions. Jedes Tool eigenes Mapping, aber gleicher Preview-/Conflict-Pfad. | mittel |

## Empfohlener naechster Sprint

### 1. Import-Sessions

Ergebnis:

- `import_sessions` und `import_records` in SQLite.
- Browser-Dateiimport und Companion-Import erzeugen Sessions.
- UI zeigt letzte Import-Sessions im Tab `Betrieb` oder `Import`.

Warum jetzt:

- Hilft bei allen Migrationen.
- Liefert Grundlage fuer Conflict Center.
- Macht grosse Browser-Imports nachvollziehbar.

### 2. Merge Undo

Ergebnis:

- Merge-Historie bekommt Undo-Button.
- Verlierer werden aus Snapshot wieder aktiv.
- Gewinner wird auf Vorher-Snapshot zurueckgesetzt.

Warum jetzt:

- Dubletten-Merge ist ein Kernversprechen.
- Undo erhoeht Vertrauen stark.

### 3. Saved Views

Ergebnis:

- Nutzer kann Sortierung, Filter, Ansicht und sichtbare Felder als Standard
  speichern.
- LinkVault startet direkt in der bevorzugten Arbeitsansicht.

Warum jetzt:

- Verbessert Alltagstauglichkeit ohne schweren Backend-Umbau.
- Passt zu linkding als schnellem Pflege-Vorbild.

## Bewusst spaeter

- Screenshot/PDF/Single-HTML.
- AI-Tagging.
- Destruktiver Browser-Sync.
- PostgreSQL/Meilisearch/Tantivy.
- Go-Port.
- Offizielle community-scripts.org-Einreichung.

Diese Punkte sind wertvoll, aber sie werden besser, wenn Import-Sessions,
Conflict Center, Undo und Betrieb zuerst stabil sind.


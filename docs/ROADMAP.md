# ROADMAP.md

## LinkVault Roadmap

**Stand:** 2026-04-28  
**Projekt:** LinkVault  
**Ausrichtung:** self-hosted Bookmark-, Favoriten-, Link-Management-, Dedup- und Sync-Plattform

---

## 0. Produktmission

LinkVault ist primär ein:

- Bookmark-Manager
- Favoriten-Manager
- Link-Organisationssystem
- Dubletten-Bereinigungswerkzeug
- Import-/Export- und Sync-fähiges Selfhost-Produkt

### Hauptziele
LinkVault soll besonders gut sein bei:

- schnellem Speichern von Links
- Verwalten großer Bookmark-Sammlungen
- Favoriten pflegen
- Tags, Lists und Collections organisieren
- Suche, Filter und Sortierung
- Bulk-Aktionen
- Duplikate erkennen, prüfen, zusammenführen und optional entfernen
- verlustarmem Import und Export
- kontrollierten sync-nahen Workflows
- leichtem Betrieb auf Proxmox VE / Debian LXC

### Nicht die Hauptmission
LinkVault ist **nicht primär**:

- ein Read-later-Produkt
- eine Reader-App
- ein Webarchiv als Hauptprodukt
- eine Knowledge Base
- ein Notiztool mit Bookmark-Nebenfunktion

Reader-, Archiv- oder AI-Funktionen dürfen später optional ergänzt werden, aber sie dürfen diese Roadmap **nicht dominieren**.

---

## 1. Roadmap-Prinzipien

### 1.1 Bookmark first
Alles, was die alltägliche Bookmark-Verwaltung spürbar verbessert, hat Vorrang.

### 1.2 Safe by default
Import, Dedup, Merge, Restore und sync-nahe Flows müssen sicher, reviewbar und nachvollziehbar sein.

### 1.3 UI/GUI ist keine Nebensache
Navigation, Such-/Filterbarkeit, Favoritensteuerung, Bulk-Aktionen und Duplicate-UX sind Kernqualität, nicht bloß Kosmetik.

### 1.4 Selfhost-Realität zählt
Der Standardpfad bleibt leicht, robust und LXC-freundlich.

### 1.5 Schweres nur optional
Archive Worker, Reader-Extrakte, Screenshots/PDF, AI oder schwere Plattformdienste bleiben optionale spätere Erweiterungen.

---

## 2. Aktuelle strategische Einschätzung

### Stark vorhanden
- Core-Bookmark-Logik
- URL-Normalisierung
- Metadatenbasis
- Favoriten / Tags / Collections / Saved Views
- Duplicate Preflight
- Dedup-Dry-Run / Merge-Richtung / sichere Merge-Philosophie
- Import-/Preview-Denken
- Companion-/Browser-Nähe
- Proxmox-/LXC-Betrieb
- Backup/Restore/Update

### Größte sichtbare Lücken
- bookmark-zentrierte Hauptnavigation
- klare Hauptarbeitsoberfläche
- Quick-Add-Alltagsfluss
- starke Favoriten-/Listen-/Collections-/Tags-UX
- sichtbares Duplicate Center
- breiterer Import-/Export-/Migrationspfad
- konsistente GUI-Architektur

---

## 3. Prioritätsreihenfolge

Die Roadmap folgt dieser Reihenfolge:

1. **Bookmark-Arbeitsoberfläche**
2. **Quick-Add + Inbox + Favoriten + Organisation**
3. **Duplicate Center + sichere Dublettenpflege**
4. **Import / Export / Migration**
5. **Sync-nahe Konflikt- und Rückimport-Flows**
6. **Betriebsreife / Proxmox / community-scripts**
7. **Optionale Erweiterungen**
8. **Archiv-/Reader-/AI-Themen nur später**

---

## 4. Phasen

---

## Phase 0 — Fundament und Betrieb
**Ziel:** LinkVault zuverlässig installierbar, wartbar und testbar halten.

### Zielbild
- stabiler Python-/SQLite-Kern
- sauberer Debian-/LXC-Betrieb
- zuverlässige Backup-/Restore-/Update-Pfade
- testbare Betriebswerkzeuge
- klare Entwicklungsumgebung

### Enthalten
- Installationspfad
- systemd-Betrieb
- Datenpfade
- Backup / Restore
- Update
- Helper
- Requirements-Check
- Proxmox-/LXC-Smoke-Tests
- Windows-/Dev-Doku

### Fertig, wenn
- frische Installation reproduzierbar läuft
- Healthcheck stabil ist
- Backup/Restore nachvollziehbar testbar ist
- Update-Pfad nicht fragil ist

### Nachrangig in dieser Phase
- kosmetische Admin-Erweiterungen
- schwere Plattformdienste
- Archiv-Worker

---

## Phase 1 — Bookmark-Kern
**Ziel:** LinkVault wird klar als Bookmark- und Favoriten-Manager nutzbar.

### Kernfunktionen
- Bookmarks speichern
- Metadaten laden
- Inbox
- Favoriten
- Pins
- Tags
- Lists / Collections
- Suche
- Filter
- Sortierung
- Saved Views
- Bulk-Aktionen
- Inline-/Detail-Bearbeitung

### Wichtige UX/GUI-Ziele
- klare Sidebar oder gleichwertige Hauptnavigation
- Bereiche für:
  - Inbox
  - All Bookmarks
  - Favourites
  - Lists / Collections
  - Tags
  - Duplicates
  - Import / Export
  - Archive
  - Settings / Profile / Admin
- schnelle Bookmark-Liste
- sichtbare Filter
- sichtbare Favoritensteuerung
- brauchbare Compact-/Detailed-/Grid-Ansichten

### Hohe Priorität in Phase 1
- Quick-Add-Modal
- Inbox-Default
- Favoritenansicht
- Bulk-Favorisieren / Bulk-Tags / Bulk-Collections
- gespeicherte Sortierung / Standardansicht
- klare Listen-/Collections-/Tags-Operabilität

### Fertig, wenn
- LinkVault sich im Alltag als Bookmark-Arbeitsoberfläche anfühlt
- neue Links schnell und ohne Reibung erfasst werden können
- Favoriten und Organisation sichtbar und leicht nutzbar sind

---

## Phase 2 — Dubletten-Erkennung und Bereinigung
**Ziel:** LinkVault wird ein außergewöhnlich gutes Tool zur sicheren Dublettenpflege.

### Kernfunktionen
- Duplicate Preflight beim Speichern
- exakte URL-Erkennung
- normalisierte URL-Erkennung
- ähnliche Kandidaten
- Dry-Run
- Merge-Plan
- Gewinner-Vorschlag
- Feldvergleich
- Undo-/Historienrichtung
- Merge ohne blindes Löschen
- markierte Verlierer statt sofortiger Datenvernichtung

### Duplicate Center
Eine dedizierte Oberfläche für:
- Dublettengruppen
- Sortierung nach Score / Risiko
- Bulk-Modi:
  - sicher
  - review
  - ähnlich
- Sichtbarkeit von:
  - Tags
  - Collections
  - Favoritenstatus
  - Notizen
  - Importherkunft
  - Metadatenunterschieden

### Wichtige nächste Schritte
- Duplicate Center UI fertigziehen
- Safe Remove als bewusste Aktion
- Merge-Historie verbessern
- Pflege-Score ergänzen
- tote Favoriten / kaputte Links in Pflegeflows integrieren

### Nicht tun
- keine harte automatische Löschung im Standardfluss
- keine stille Überschreibung

### Fertig, wenn
- Dublettenpflege nicht nur technisch, sondern UI-seitig klar und sicher ist
- Nutzer große Bibliotheken kontrolliert bereinigen können

---

## Phase 3 — Import / Export / Migration
**Ziel:** LinkVault wird ein starkes Zielsystem für Browser- und Tool-Migrationen.

### Import-Ziele
- HTML als Baseline
- Chromium-JSON
- Firefox-JSON / JSONLZ4
- Safari-ZIP
- später weitere Tool-Importer

### Import-Grundsätze
- Vorschau vor Commit
- Dublettenprüfung vor Import
- Konfliktanzeige
- Rohdaten-Erhalt
- Herkunft sichtbar halten:
  - Browser
  - Profil
  - Datei
  - Pfad
  - Zeitstempel
  - Import-Session

### Export-Ziele
- allgemeiner Bookmark-Export
- gefilterter Export
- browserfreundliche Strukturen
- stabile Rückimport-Basis

### Hohe Priorität
- HTML-Import robust halten
- Vendor-Enrichment Schritt für Schritt ausbauen
- generischer CSV-/JSON-Import
- Tool-Importe später gezielt ergänzen

### Fertig, wenn
- Import nicht nur „Daten rein“, sondern sauberer Migrationsworkflow ist
- Nutzer nachvollziehen können, was importiert, gemerged oder übersprungen wird

---

## Phase 4 — Companion Extension und sync-nahe Flows
**Ziel:** Browser und LinkVault arbeiten kontrolliert zusammen.

### Companion-Ziele
- aktuellen Tab speichern
- Browser-Bookmarks lesen
- Import-Vorschau senden
- Browser-Rückimport mit Vorschau
- Duplicate Preflight auch in Extension-Flows
- strukturierte Konfliktanzeige

### Sync-nahe Grundsätze
- kein blinder Zwei-Wege-Sync
- kein automatisches Löschen
- keine stillen Überschreibungen
- Konflikte sichtbar
- Entscheidungen nachvollziehbar
- Import ist nicht automatisch Backup
- Restore ist nicht automatisch Sync

### Wichtige nächste Schritte
- Duplicate-/Konflikt-UX in der Extension stärken
- gefilterten Export sauber halten
- Drift-/Snapshot-Logik dort verbessern, wo sie Bookmark-Nutzen hat
- Browser-Metadaten sauber erhalten

### Nicht tun
- keine magische Hintergrundsynchronisation ohne Vorschau
- keine Reader-/Archiv-Logik in die Extension verschieben

### Fertig, wenn
- die Extension LinkVault klar als Bookmark-/Import-/Export-/Dedup-Werkzeug ergänzt

---

## Phase 5 — Profile, Admin, Mehrbenutzer-Grundlagen
**Ziel:** Solide, kleine Multi-User-Basis ohne Produktdrift.

### Enthalten
- Admin/User-Rollen
- user-scoped settings
- Profilbereich
- Admin-Bereich
- API-Token-Verwaltung
- Passwortwechsel / Reset
- saubere Trennung von:
  - persönlichem Bereich
  - Admin
  - Operations

### Wichtig
Diese Phase bleibt dem Bookmark-Kern untergeordnet.

### Nicht Hauptfokus
- große Team-/Org-Funktionen
- SCIM / IdP
- globale Enterprise-Provisioning-Pfade

### Später möglich
- Shared Collections
- viewer/editor-Modelle pro Liste / Collection

---

## Phase 6 — Proxmox / community-scripts Reifegrad
**Ziel:** LinkVault wird ein überzeugendes Selfhost-Produkt auf Proxmox.

### Ziele
- stabiler Einzeiler
- reproduzierbare LXC-Tests
- dokumentierter Update-/Backup-/Restore-Weg
- Helper sinnvoll ausgebaut
- community-scripts-konforme Reife

### Wichtige Schritte
- Installer und Hilfsskripte konsolidieren
- Requirements-Checks klar halten
- Logs und Fehlersignale verbessern
- Helper-Funktionen stabilisieren
- Submission-Reife vorbereiten

### Nicht überpriorisieren
Wenn UI/GUI, Dedup oder Import noch wesentliche Lücken haben, geht Produktkern vor Einreichungsformalitäten.

---

## Phase 7 — Automatisierung und Regelwerk
**Ziel:** LinkVault organisiert große Bibliotheken smarter, ohne den Kern zu überladen.

### Mögliche Inhalte
- Domain-Regeln
- Pfad-Regeln
- Text-/Keyword-Regeln
- automatische Tag-/List-/Collection-Vorschläge
- Favoriten-/Prioritätsvorschläge
- Smart Collections
- Aktivitäts-/Pflegehinweise

### Grundsatz
Automatisierung soll Bookmark-Pflege verbessern, nicht das Produkt in eine AI-/Reader-/Archivmaschine verwandeln.

---

## Phase 8 — Optionale spätere Erweiterungen
**Ziel:** Zusätzliche Tiefe, ohne den Core zu belasten.

### Nur optional und nachrangig
- Reader-Extrakte
- Screenshot / PDF / Single-HTML
- AI-Zusammenfassungen
- Archive Worker
- schwere Plattformdienste
- alternative Release-Artefakte
- tiefere Sharing-/Team-Funktionen

### Bedingung
Diese Themen kommen erst, wenn:
- Bookmark-Kern stark ist
- GUI tragfähig ist
- Duplicate Center gut funktioniert
- Import-/Sync-/Migration stabil sind
- Selfhost-Betrieb nicht leidet

---

## 5. Aktuelle konkrete To-do-Reihenfolge

### Jetzt zuerst
1. bookmark-zentrierte Navigation fertigziehen
2. Hauptansicht für Bookmarks stärken
3. Quick-Add + Inbox-Flow fertigziehen
4. Favoriten-/Tags-/Lists-/Collections-UX stärken
5. Duplicate Center UI priorisieren

### Danach
6. Import-/Export-/Migrationspfade verbreitern
7. Companion-/Browser-Flows konsolidieren
8. Sync-nahe Konfliktflüsse verbessern
9. Admin/Profile sauber vervollständigen
10. Proxmox/community-scripts-Reife nachziehen

### Später
11. Regelwerk / Smart Collections
12. optionale Archive-/Reader-/AI-Erweiterungen

---

## 6. Was aktuell bewusst nicht priorisiert wird

Diese Punkte stehen bewusst **nicht** oben auf der Roadmap:

- Reader-Modus
- Webarchivierung als Hauptfunktion
- Screenshot/PDF/Single-HTML als Standardpfad
- WARC
- AI-first-Produktlogik
- große Team-/Org-Funktionen
- Enterprise-Provisioning
- Plattform-/Multi-Service-Ausbau
- Design-Spielereien ohne Bookmark-Nutzen

---

## 7. Erfolgskriterien

Die Roadmap ist auf Kurs, wenn LinkVault für Nutzer bald klar als dieses Produkt erkennbar ist:

- ein sehr guter Bookmark-Manager
- ein starkes Favoriten-Tool
- ein sauberer Link-Organizer
- ein sicheres Dubletten-Bereinigungswerkzeug
- ein zuverlässiges Import-/Export-/Sync-fähiges Selfhost-System

Nicht:
- ein halbfertiger Reader
- ein Archivsystem mit Bookmark-Nebenfunktion
- ein UI-lastiges Dashboard ohne starke Arbeitsoberfläche

---

## 8. Entscheidungsregel für neue Aufgaben

Bei jedem neuen Feature, jeder UI-Änderung und jeder Architekturidee ist zu fragen:

**Verbessert diese Änderung LinkVault klar als Bookmark-, Favoriten-, Organisations-, Dedup-, Import-/Export- und Sync-Plattform?**

Wenn die Antwort hauptsächlich lautet:
- „es macht LinkVault mehr zu einer Reader-App“
- „es macht LinkVault archivlastiger“
- „es macht LinkVault schwerer statt nützlicher“

dann ist die Priorität aktuell falsch.

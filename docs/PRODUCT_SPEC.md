# LinkVault Produktvision

## Ziel

LinkVault ist ein modernes **self-hosted Tool zum Verwalten, Organisieren, Sortieren, Kategorisieren, Synchronisieren und Bereinigen von Favoriten, Links und Bookmarks**.

Der Schwerpunkt liegt auf:

- schnellem Speichern von Links
- strukturierter Bookmark-Verwaltung
- Favoriten-Management
- Tags, Listen und Collections
- Suche, Filter und Sortierung
- Bulk-Aktionen
- verlustarmen Import-/Export-Workflows
- sicherer Dubletten-Erkennung und Dubletten-Bereinigung
- leichter, robuster Selfhosting-Bereitstellung auf Proxmox LXC

## Bewusste Abgrenzung

LinkVault ist **nicht primär**:

- ein Read-later-Tool
- eine Reader-App
- ein Webarchiv als Hauptprodukt
- eine Knowledge Base
- ein Notiztool mit Bookmark-Nebenfunktion

Read-later-, Reader- oder Archivfunktionen dürfen später optional ergänzt werden, aber sie dürfen **nicht** die Produktmission, Navigation, Datenstruktur, Roadmap oder UI dominieren.

---

## Produktkern

LinkVault ist in erster Linie ein:

- Bookmark-Manager
- Favoriten-Manager
- Link-Organisationssystem
- Dubletten-Bereinigungswerkzeug
- Sync- und Import-/Export-fähiges Selfhost-Produkt

### Kernversprechen

LinkVault soll drei Dinge besonders gut können:

1. **Bookmarks und Favoriten sauber verwalten**
2. **große Link-Sammlungen übersichtlich organisieren**
3. **Dubletten sicher erkennen, prüfen, zusammenführen oder entfernen**

---

## Inspirationsquellen

| Quelle | Übernehmen | Verbessern |
|---|---|---|
| Karakeep | Favoriten, Listen, Regeln, starke Organisation, spätere Automatisierung | klarere Bookmark-Pflege, stärkere Dubletten-Workflows |
| linkding | Minimalismus, schnelle Bedienung, Bulk-Editing, Suche, REST-API | Favoriten-/Collections-/Mehrfachorganisation |
| Linkwarden | Collections, Sub-Collections, Pinning, strukturierte Navigation | echte Dubletten- und Merge-Logik |
| LinkAce | klassische Bookmark-Verwaltung, Tags, Listen, Monitoring | modernere Bulk-/Dedup-/Sync-Flows |
| Readeck | leichter Betrieb, gute Struktur | nicht als Read-later-Hauptidentität übernehmen |
| Shiori | leichtgewichtiges Selfhosting, einfache Bedienung | stärkere Organisation, bessere Pflege-Workflows |

## Grundregel zu Referenzen

LinkVault übernimmt **Stärken**, aber nicht die komplette Identität anderer Produkte.

Insbesondere:
- keine Reader-first-Produktlinie
- keine Archiv-first-Produktlinie
- keine überladene Content-Consumption-Oberfläche

---

## Kernarbeitsbereiche

Die zentrale Informationsarchitektur von LinkVault soll bookmark-zentriert sein.

### 1. Inbox
Für neue, unsortierte oder noch nicht geprüfte Bookmarks.

### 2. All Bookmarks
Die Hauptarbeitsansicht für die gesamte Bookmark-Bibliothek.

### 3. Favourites
Eigene Ansicht für persönliche Favoriten.

### 4. Lists / Collections
Strukturierte Organisation über Listen, Sammlungen und ggf. Unterstrukturen.

### 5. Tags
Flexible Mehrfach-Kategorisierung über Schlagworte.

### 6. Duplicates
Eigene Pflegezentrale für Dubletten-Erkennung, Prüfung, Merge und optionales Entfernen.

### 7. Import / Export
Dedizierter Bereich für Browser-Importe, Tool-Importe, Vorschau, Konflikte und Exporte.

### 8. Archive
Sekundärer Bereich für archivierte oder bewusst ausgeblendete Bookmarks.  
Nicht als Hauptproduktfläche.

### 9. Settings / Profile / Admin
Klar getrennte Bereiche für Benutzerprofil, API-Token, Integrationen und Administration.

---

## Kernfunktionen

## 1. Bookmarks speichern und verwalten

LinkVault speichert Bookmarks mit mindestens:

- URL
- Titel
- Beschreibung
- Domain
- Favicon
- Erstellungs-/Importzeitpunkt
- Favoritenstatus
- Tags
- Listen / Collections
- Notizen
- Quelle / Herkunft

### Schnelles Speichern
- Quick Add mit Fokus auf URL
- Standardziel z. B. Inbox
- sofortige Duplikat-Prüfung
- optionale Direktzuweisung von Tags / Liste / Favorit

---

## 2. Favoriten

Favoriten sind eine Kernfunktion, nicht nur ein kleines Flag.

### Anforderungen
- eigener Favoritenbereich
- Favorit schnell umschaltbar
- Filter nach Favoriten
- Bulk-Favorisieren / Bulk-Entfernen
- Favoritenstatus sichtbar in Listen- und Detailansicht

### Ziel
Favoriten sollen sich wie ein echter Arbeitsbereich anfühlen, nicht wie eine versteckte Nebeneigenschaft.

---

## 3. Organisation: Tags, Listen, Collections

LinkVault organisiert Bookmarks über mehrere Ebenen:

### Tags
- flexible Mehrfach-Labels
- ideal für Themen, Status, Kontexte

### Lists
- kuratierte, manuelle Gruppierung
- ein Bookmark kann mehreren Listen zugeordnet werden

### Collections
- strukturierende Oberkategorie / Container
- optional mit Unterebenen

### Saved Views
- gespeicherte Filter-/Sortier-/Ansichtskombinationen
- nutzerbezogen speicherbar

### Regeln und Automatisierung
Später optional:
- Domain-Regeln
- Pfad-Regeln
- Text-/Keyword-Regeln
- Vorschläge für Tag / Liste / Collection / Favorit

Regeln dienen der Bookmark-Organisation, nicht dem Aufbau einer Reader-/Archivplattform.

---

## 4. Dubletten-Erkennung und Dubletten-Bereinigung

Dublettenbehandlung ist eine der wichtigsten Kernfunktionen von LinkVault.

### Ziele
- doppelte Links früh erkennen
- unnötige Dubletten vermeiden
- vorhandene Daten nicht verlieren
- sichere Review vor Änderungen
- Massenbereinigung kontrolliert ermöglichen

### Erkennung
LinkVault soll Dubletten mindestens auf diesen Ebenen erkennen:

- exakte URL
- normalisierte URL
- Canonical-/Redirect-Ziel
- ähnliche URL auf derselben Domain
- spätere heuristische Kandidatengruppen

### Duplicate Preflight
Vor dem Speichern oder Importieren wird geprüft:

- existiert dieselbe URL schon?
- existiert dieselbe normalisierte URL?
- gibt es wahrscheinliche Kandidaten?

Wenn ja, soll der Nutzer:
- vorhandenen Bookmark öffnen
- vorhandenen Bookmark aktualisieren
- bewusst separat speichern
- Merge-/Review-Workflow starten

### Dedup Center
Eine eigene Oberfläche für Dublettenpflege mit:

- Dublettengruppen
- Gewinner-Vorschlag
- Feldvergleich
- Merge-Plan
- Dry-Run
- Statusanzeige
- Undo-/Historien-Konzept

### Merge-Grundsätze
Beim Merge dürfen wichtige Daten nicht verloren gehen:

- Tags
- Listen / Collections
- Favoritenstatus
- Pin-Status
- Notizen
- bessere Titel/Beschreibungen
- Importquelle
- Redirect-/Herkunftskontext

### Entfernen von Dubletten
Dubletten dürfen entfernt werden, aber nur:
- bewusst
- nachvollziehbar
- nach Review
- nie blind automatisch im Standardfluss

### Standardprinzip
**Safe by default.**
Kein hartes Löschen ohne ausdrückliche Entscheidung.

---

## 5. Suche, Filter und Sortierung

LinkVault soll sich für große Bookmark-Sammlungen eignen.

### Suche
- Volltextsuche
- URL-/Domain-Suche
- Tag-/List-/Collection-Filter
- Kombinierbarkeit von Filtern

### Sortierung
- nach Titel
- nach Domain
- nach hinzugefügt
- nach geändert
- nach Favorit
- nach Pin
- nach Pflege-/Deduplikationsstatus
- nach Importzeitpunkt
- später optional nach Nutzungssignalen

### Pflegesichten
Beispiele:
- neue Links prüfen
- Dubletten bereinigen
- fehlende Tags ergänzen
- kaputte Links prüfen
- Favoriten pflegen

---

## 6. Bulk-Aktionen

Bulk-Operationen sind Pflicht für ernsthafte Bookmark-Verwaltung.

Mindestens:
- Tags hinzufügen / entfernen
- Listen / Collections zuweisen
- Favorisieren / entfavorisieren
- Archivieren
- Löschen
- Dublettenprüfung anstoßen
- Merge-Review vorbereiten
- Exportieren

Bulk-Aktionen müssen klar sichtbar, sicher und verständlich sein.

---

## 7. Import / Export / Migration

Import und Export sind Kernfunktionen, nicht nur Behelfslösungen.

### Import-Ziele
- Browser-Bookmarks
- HTML als universelle Baseline
- später reichere Vendor-Formate
- Tool-Importe in späteren Phasen

### Import-Grundsätze
- Vorschau vor Commit
- Konfliktanzeige
- Dublettenprüfung
- Rohdaten-Erhalt für unbekannte Felder
- sichere Merge-/Create-/Update-Entscheidungen

### Export
- normale Bookmark-Exporte
- gefilterte Exporte
- browserfreundliche Exportpfade
- spätere migrationsfreundliche Formate

### Ziel
LinkVault soll Browser- und Tool-Wechsel erleichtern, ohne Metadaten unnötig zu verlieren.

---

## 8. Synchronisierung

Synchronisierung ist ein Zielthema, aber kontrolliert und nachvollziehbar.

### Wichtige Prinzipien
- Sync darf nie blind Daten zerstören
- Import ist nicht automatisch Backup
- Restore ist nicht automatisch Zwei-Wege-Sync
- Konflikte müssen sichtbar sein
- Dubletten und Sync-Konflikte hängen zusammen

### Roadmap-Richtung
- extension-gestützte Browser-Flows
- serverseitige Vorschau
- konfliktbewusste Sync-/Restore-Logik
- später ausbaubare echte Sync-Pfade

---

## 9. Selfhosting und Betrieb

LinkVault soll im Standardpfad leicht, robust und gut wartbar bleiben.

### Betriebsziele
- Debian / Proxmox LXC freundlich
- SQLite + FTS5 im Kern
- geringer Ressourcenbedarf
- einfacher Update-/Backup-/Restore-Pfad
- gut testbarer Installationsweg
- klare lokale Admin-Werkzeuge

### Grundsatz
Der Core bleibt klein und effizient.  
Schwere Zusatzfunktionen werden nicht zum Standardzwang.

---

## 10. UI / UX / GUI Zielbild

LinkVault soll sich wie ein echtes Bookmark-Arbeitswerkzeug anfühlen.

### UI-Ziele
- klare Navigation
- Sidebar oder ähnlich starke Hauptstruktur
- sichtbare Hauptbereiche
- starke Bookmark-Liste / Detailansicht
- schnelle Suche
- klare Filter
- gut erkennbare Favoriten
- klare Bulk-Aktionen
- sichtbarer Dublettenbereich

### UX-Ziele
- schneller Standardfluss
- geringer Reibungsverlust
- gute Pflege großer Bibliotheken
- vertraute Bookmark-Muster aus Browsern und Referenztools
- keine Reader-zentrierte Hauptfläche

### GUI-Ziele
- brauchbare Tabellen-/Listen-/Kartenansichten
- gute Zustände für Auswahl, Laden, Fehler, Konflikte
- klare Dialoge für Import und Merge
- keine kosmetische Spielerei ohne Bookmark-Mehrwert

---

## Bewusst nachrangig

Diese Themen dürfen später kommen, sind aber nicht Hauptmission:

- Reader-Modus
- Webarchivierungstiefe
- Screenshot/PDF/Single-HTML als Standard
- WARC
- AI-Zusammenfassungen
- schwere Crawler-/Worker-Stacks
- Enterprise-Provisioning
- große Team-/Org-Funktionen

Wenn eines dieser Themen die Bookmark-Verwaltung verdrängt, ist das eine Fehlentwicklung.

---

## Kurzform der Produktformel

```text
linkding-artige Klarheit und Geschwindigkeit
+ Karakeep-artige Organisation, Listen und Regeln
+ Linkwarden-artige Collections und strukturierte Navigation
+ LinkAce-artige Verwaltungsreife
+ Shiori-/Readeck-artige Leichtgewichtigkeit im Betrieb
+ starke eigene Dubletten-Erkennung, Review und sichere Bereinigung
+ selfhosted Proxmox-LXC-Tauglichkeit

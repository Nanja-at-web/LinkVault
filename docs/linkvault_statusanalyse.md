# LinkVault - bereinigte Statusanalyse

**Stand:** 28. April 2026  
**Projekt:** <https://github.com/Nanja-at-web/LinkVault>

## Zweck dieser Statusanalyse

Diese Datei bewertet den aktuellen Projektstand von **LinkVault** so, dass die Produktprioritäten konsistent zur aktuellen Projektmission bleiben.

### Verbindliche Produktlinie

LinkVault ist primär ein:

- self-hosted Bookmark-Manager
- Favoriten-Manager
- Link-Organisationssystem
- Dubletten-Bereinigungswerkzeug
- Import-/Export- und Sync-fähiges Selfhost-Produkt

LinkVault ist **nicht primär**:

- ein Read-later-Produkt
- eine Reader-App
- ein Webarchiv als Hauptprodukt
- eine Knowledge Base
- ein Notiztool mit Bookmark-Nebenfunktion

Archiv-, Reader- oder Webarchive-Funktionen dürfen später optional ergänzt werden, sind aber **nicht** die Hauptmission.

---

## Kurzfazit

LinkVault ist technisch und betrieblich bereits stärker als die sichtbare Hauptoberfläche vermuten lässt.

Die größten Stärken liegen aktuell in:

- dedup-/merge-orientierter Datenpflege
- Import-/Restore-/Konfliktlogik
- Proxmox-/LXC-Betriebsfähigkeit
- Backup/Restore/Update
- Bookmark-Metadaten und Browser-/Extension-Nähe
- strukturiertem Projektdenken und solider Dokumentation

Die größte sichtbare Schwäche bleibt:

- die **Hauptoberfläche**
- die **Navigationsarchitektur**
- die **klare bookmark-zentrierte Arbeitsansicht**
- die **Favoriten-/Listen-/Collections-/Tags-Operabilität im Frontend**
- die **sichtbare, alltagstaugliche Dublettenpflege im UI**

Kurz gesagt:

**Backend, Betriebsfähigkeit und Datenlogik sind vielerorts weiter als das Produktgefühl in der Oberfläche.**

---

## Strategische Korrektur

Frühere Dokumente und Zwischenstände haben LinkVault teils zu stark in Richtung:

- Archivierung
- Restore-/Konfliktzentrum
- Read-later-Nähe
- sekundäre Admin-/Systemthemen

gezogen.

Diese Statusanalyse korrigiert das.

### Neue Prioritätsregel

Wenn eine Aufgabe nicht dazu beiträgt, LinkVault als **besseren Bookmark-/Favoriten-/Link-Manager mit Dublettenbehandlung und Sync-Fähigkeit** zu machen, dann ist sie aktuell nachrangig.

---

## Kernaussagen zum Produktstatus

### 1. Der Bookmark-Kern ist substanziell vorhanden

Bereits sichtbar oder dokumentiert vorhanden sind wesentliche Grundlagen für den Bookmark-Kern:

- Bookmarks speichern
- URL-Normalisierung
- Metadaten-Ermittlung
- Favoriten
- Tags
- Collections / Listen-Strukturen
- Volltextsuche
- Filterung
- Saved Views
- Import-Vorschau
- Browser-/Extension-Anbindung
- Bulk-nahe Datenpflege
- dedup-/merge-orientierte Logik

Das ist eine starke Grundlage.

### 2. Dublettenbehandlung ist bereits eine echte Kernstärke

LinkVault hat bei der Dublettenlogik schon jetzt ein Profil, das über viele Referenztools hinausgehen kann.

Vorhanden oder geplant im Kern:

- URL-Normalisierung
- Duplicate Preflight
- Dry-Run
- Merge ohne blindes Löschen
- Merge-Historie / Undo-Richtung
- Konfliktorientierte Review
- sichere Merge- und Pflege-Workflows
- Erhalt wichtiger Daten statt destruktiver Bereinigung

### 3. Infrastruktur und Selfhosting sind ungewöhnlich weit

Für ein noch junges Projekt ist die Betriebsseite stark:

- Proxmox LXC
- Debian-LXC-Installationspfad
- Backup/Restore
- Update-Skripte
- Helper-Werkzeuge
- Healthchecks
- reproduzierbare Testwege

Das ist ein klarer Vertrauensfaktor.

### 4. Die Produktidentität ist im UI noch nicht klar genug sichtbar

Der größte Mangel ist nicht nur „fehlende Optik“, sondern eine fehlende oder zu schwache bookmark-zentrierte Hauptarbeitsoberfläche.

Die sichtbare Oberfläche muss deutlicher zeigen:

- wo neue Bookmarks landen
- wo Favoriten liegen
- wie Tags / Lists / Collections gepflegt werden
- wo Dubletten aktiv bearbeitet werden
- wie Import / Export / Sync alltagsnah bedienbar sind

---

## Aktueller Stärkenblock

## A. Daten- und Pflegequalität

Stark oder vielversprechend:

- nicht-destruktive Dublettenlogik
- Merge statt blindem Löschen
- Herkunfts- und Konfliktbewusstsein
- saubere Import-Vorschau
- nachvollziehbare Status-/Pflegeflüsse

## B. Betriebsqualität

Stark:

- Proxmox-/LXC-Fokus
- Backup-/Restore-/Update-Fähigkeit
- Helper/Operations-Denken
- geringer Core-Anspruch an die Laufzeitumgebung

## C. Produktbasis

Stark:

- klare Referenztool-Auswertung
- sinnvolle Orientierung an Karakeep, linkding, Linkwarden, LinkAce, Readeck, Shiori
- erkennbare Strategie für Bookmark-Organisation und Datenpflege

---

## Größte Schwächen / Lücken

## 1. UI / GUI / Navigation

Die wichtigste offene Produktlücke ist die Hauptoberfläche.

Es fehlt noch eine durchgehend starke bookmark-zentrierte Arbeitsfläche mit:

- klarer Sidebar oder gleichwertiger Primärnavigation
- deutlicher Trennung von Inbox / All Bookmarks / Favourites / Lists / Collections / Tags / Duplicates / Import / Settings
- schneller Favoritensteuerung
- klar sichtbaren Bulk-Aktionen
- guter Listen-/Tabellen-/Kartenlogik
- schneller Sortierung und Filterung
- deutlichem Duplicate-Center

## 2. Quick-Add / Alltagseinstieg

Es fehlt ein ausreichend schneller, alltagstauglicher Standardfluss für:

- neuen Link speichern
- direkt in Inbox landen
- optional schnell favorisieren
- optional mit Tags / Liste / Collection versehen
- sofortige Duplicate-Warnung

## 3. Favoriten- und Organisations-UX

Favoriten, Tags, Lists und Collections müssen sich wie **echte Arbeitsbereiche** anfühlen.

Nicht ausreichend ist:
- sie nur als Datenfelder zu besitzen

Sie müssen im Produktalltag leicht nutzbar sein.

## 4. Dedup-UX im Frontend

Die Datenlogik ist stark, aber die Dublettenpflege muss im UI noch sichtbarer und verständlicher werden:

- eigene Dublettenansicht
- Kandidatengruppen
- Feldvergleich
- Gewinner-Vorschlag
- Merge-Plan
- Safe Remove
- Undo-/Historienhinweise
- Bulk-Bereinigungsmodi

## 5. Migrationen / Importbreite

Import ist schon klar als Kernrichtung erkennbar, aber noch nicht breit genug fertig.

Wichtige nächste Ausbaurichtung:
- HTML als universelle Baseline gut halten
- Vendor-Enrichment ausbauen
- Browserformate erweitern
- Tool-Importe später ergänzen
- Rohdaten-Erhalt und Konfliktlogik stabil halten

---

## Was aktuell NICHT zum Hauptfokus werden sollte

Folgende Themen sind aktuell bewusst nachrangig:

- Reader-Extrakte
- Screenshot/PDF/Single-HTML als Standard
- WARC
- große Archiv-Worker als Kernelement
- AI-Zusammenfassungen
- Enterprise-/Provisioning-Themen
- breite Team-/Org-Funktionen
- große Plattform-/Multi-Service-Ausweitung

Diese Themen sind nicht verboten, aber sie dürfen den Bookmark-Kern nicht verdrängen.

---

## Status nach Arbeitsbereichen

| Bereich | Status | Bewertung |
|---|---:|---|
| Fundament / Selfhosting | hoch | bereits ungewöhnlich stark |
| Bookmark-Kern | hoch | solide Basis, gute Richtung |
| Favoriten / Organisation | mittel | Datenlogik da, UX/UI noch ausbauen |
| Suche / Filter / Views | mittel bis hoch | gute Basis, muss UI-seitig stärker werden |
| Dublettenlogik | hoch | Kernstärke |
| Dubletten-UI | mittel | deutlich ausbaufähig |
| Import / Migration | mittel | strategisch richtig, noch ausbauen |
| Sync-nahe Flows | mittel | hilfreich, aber Kernziel nicht überlagern |
| Archivierung | niedrig | bewusst nachrangig |
| Admin / Profile / Betrieb | mittel bis hoch | wichtig, aber nicht die Produktmitte |
| Frontend-Navigation / GUI | kritisch offen | aktuell größte sichtbare Lücke |

---

## Priorisierte nächste Schritte

## Priorität 1 — sichtbare Bookmark-Arbeitsoberfläche stärken

Als Nächstes sollte LinkVault vor allem im UI/GUI spürbar besser werden.

### Ziel
Eine Oberfläche, die sofort als Bookmark-/Favoriten-/Link-Manager erkennbar ist.

### Besonders wichtig
- klare Sidebar / Navigation
- klare Hauptansicht für Bookmarks
- starke Suche und Filter
- sichtbare Favoritensteuerung
- sichtbare Listen / Collections / Tags
- klare Bulk-Aktionen
- sichtbarer Duplicate-Bereich

## Priorität 2 — Quick-Add und Inbox-Flow

Der Alltagseinstieg muss leichter werden.

### Ziel
Neue Links sollen ohne Reibung erfasst und später sauber organisiert werden.

## Priorität 3 — Duplicate Center UX

Dublettenpflege ist eine Kernstärke von LinkVault und sollte auch als solche erlebbar sein.

### Ziel
Dubletten nicht nur technisch gut behandeln, sondern UI-seitig klar und sicher pflegbar machen.

## Priorität 4 — Favoriten / Lists / Collections / Tags operativ ausbauen

Diese Organisationsachsen müssen im Alltag stark werden.

### Ziel
LinkVault soll sich nicht nur nach „Datenmodell“ anfühlen, sondern nach echter Arbeitsumgebung.

## Priorität 5 — Import-/Migrationsbreite erweitern

HTML-Basis halten, Vendor-Enrichment ausbauen, Vorschau-/Konfliktlogik stärken.

## Priorität 6 — Sync-/Restore-/Conflict-Flows gezielt einordnen

Diese Systeme bleiben wichtig, aber nur als Unterstützung für Bookmark-Management und sichere Migration.

---

## Konkrete aktuelle Produktreihenfolge

Die derzeit sinnvollste Reihenfolge ist:

1. UI/GUI-Navigation und Hauptoberfläche bookmark-zentriert fertigziehen
2. Quick-Add / Inbox / Favoriten / Listen / Collections / Tags im Alltag stärken
3. Duplicate Center sichtbar und stark machen
4. Import-/Export-/Migrationspfade erweitern
5. Sync-/Restore-/Conflict-Flows dort verbessern, wo sie Bookmarks und Migration wirklich helfen
6. Proxmox-/community-scripts-Reife weiter erhöhen
7. Archiv-/Reader-Themen erst danach optional ausbauen

---

## Empfehlung

Wenn man nur fragt:

**„Was bringt LinkVault jetzt am weitesten in Richtung eines starken Produkts?“**

dann lautet die Antwort:

### Nicht zuerst:
- mehr Archivtiefe
- mehr Reader-Funktionen
- mehr schwere Plattformtechnik

### Sondern zuerst:
- bessere Bookmark-Arbeitsoberfläche
- stärkere Favoriten-/Organisations-Workflows
- sichtbare und sichere Dublettenpflege
- schnellerer Alltagseinstieg
- robuste Import-/Sync-Grundlage

---

## Endbewertung

LinkVault ist aktuell **kein unfertiger Ideenhaufen**, sondern bereits ein ernstzunehmendes Bookmark-/Dedup-/Selfhost-Projekt mit guter technischer Basis.

Der aktuelle Engpass ist nicht:
- fehlendes Denken
- fehlende Betriebsfähigkeit
- fehlende dedup-orientierte Datenlogik

Der Engpass ist vor allem:
- **sichtbare Produktführung in der Oberfläche**
- **klare bookmark-zentrierte Navigation**
- **starke Alltags-Workflows für Favoriten, Organisation und Dublettenpflege**

## Endsatz

LinkVault sollte jetzt nicht breiter, sondern **klarer** werden:

- klarer als Bookmark-Manager
- klarer als Favoriten-Tool
- klarer als Dubletten-Bereinigungswerkzeug
- klarer als selfhosted Sync-/Import-/Export-Plattform

Nicht klarer als Reader oder Archivsystem.

# LinkVault

LinkVault ist eine self-hosted Plattform zum Verwalten von Bookmarks, Favoriten und Links – mit starker Dublettenbehandlung, Import-/Export-Workflows und leichtgewichtigem, Proxmox-freundlichem Betrieb.

## Was LinkVault ist

LinkVault ist für Menschen gedacht, die:

- Links schnell speichern wollen
- Bookmarks und Favoriten verwalten möchten
- große Link-Sammlungen mit Tags, Listen und Collections organisieren wollen
- effizient suchen, filtern und sortieren möchten
- Dubletten sicher erkennen, prüfen, zusammenführen und optional entfernen wollen
- Bookmarks aus Browsern und anderen Tools importieren möchten
- das gesamte System leichtgewichtig self-hosted betreiben wollen

## Was LinkVault nicht ist

LinkVault ist **nicht primär**:

- eine Read-later-App
- ein Reader-First-Produkt
- ein Webarchiv als Hauptprodukt
- eine Knowledge Base
- ein Notiztool mit Bookmark-Nebenfunktion

Archiv- oder Reader-nahe Funktionen können später optional ergänzt werden, sind aber nicht die Hauptausrichtung des Produkts.

---

## Warum LinkVault existiert

Viele self-hosted Bookmark-Tools zwingen zu einem Kompromiss:

- entweder leichtgewichtig und einfach
- oder funktionsreich, aber schwerer und weniger auf Pflege und Migration ausgerichtet

LinkVault soll genau diese Lücke schließen.

Die zentralen Stärken sind:

- starke Bookmark- und Favoriten-Verwaltung
- sichtbare Dublettenprüfung und Dublettenbereinigung
- saubere Import-/Export- und Migrations-Workflows
- browsernahe Metadatenbehandlung
- sichere, nachvollziehbare Merge-Logik
- leichtgewichtiger Selfhost-Betrieb auf Proxmox VE / Debian LXC

---

## Aktueller Fokus

Der aktuelle Produktfokus liegt auf:

- Bookmark-Speicherung und Bearbeitung
- Favoriten, Pins, Tags, Collections und Notizen
- Volltextsuche mit SQLite FTS5
- Bulk-Aktionen
- Duplicate Preflight vor dem Speichern
- Dublettenprüfung, Dry-Run und Merge ohne blindes Löschen
- Import-Vorschau und sichere Migration
- Browser-Companion-Workflows
- Proxmox-freundlichem Installations-, Update-, Backup- und Restore-Pfad

---

## Aktueller Funktionsumfang

### Bookmark-Verwaltung
- Links mit URL-Normalisierung speichern
- Metadaten wie Titel, Beschreibung, Favicon und Domain laden
- Bookmarks in der UI bearbeiten
- Favoriten und Pins verwalten
- Tags, Collections und Notizen vergeben
- mit Inbox-ähnlichen unsortierten Bookmarks arbeiten
- Saved Views und mehrere Anzeigeformen nutzen

### Suche, Filter und Organisation
- SQLite-FTS5-Volltextsuche
- Filter für Favoriten, Pins, Domain, Tags, Collections und Status
- Compact-, Detailed- und Grid-Ansichten für Bookmarks
- Bulk-Aktionen für Tags, Collections, Favoriten und Pins

### Dublettenbehandlung
- exakte Dublettenerkennung
- Dublettenerkennung über normalisierte URLs
- Duplicate Preflight vor dem Speichern
- Dubletten-Dashboard mit Dry-Run
- Gewinner-Vorschlag und Feldvergleich
- Merge ohne blindes hartes Löschen
- Merge-Historie / Undo-Richtung
- markierte gemergte Dubletten statt stiller destruktiver Bereinigung

### Import und Migration
- Browser-HTML-Import mit Vorschau
- Chromium-JSON-Importpfad
- Import-Session-Metadaten
- Dubletten- und Konfliktbewusstsein beim Import
- herkunftsbewusste Richtung für spätere breitere Migrationen

### Companion Extension
- aktuellen Tab speichern
- Browser-Bookmarks lesen
- Bookmark-Vorschauen an LinkVault senden
- sicherer Browser-Rückimport mit Vorschau
- dubletten- und konfliktbewusste Browser-Roundtrips

### Selfhosting und Betrieb
- Python + SQLite + FTS5 im Kern
- Proxmox VE / Debian LXC freundlicher Deployment-Pfad
- Helper-Befehle für Health, Update, Backup und Restore
- dokumentierter Update-Pfad
- dokumentierter Backup-/Restore-Pfad
- reale LXC-Smoke-Test-Richtung

---

## Produktrichtung

LinkVault wird um fünf Kernsäulen herum gebaut:

1. Bookmark-Verwaltung
2. Favoriten als Konzept erster Klasse
3. starke Organisation mit Tags, Listen und Collections
4. sichere Dublettenprüfung und Dublettenbereinigung
5. Import/Export und sync-nahe Browser-Workflows

Alles andere ist nachrangig.

---

## Dubletten-Philosophie

LinkVault behandelt Dubletten nicht nur als Import-Warnung, sondern als echte Produktfunktion.

### Kernprinzipien
- Dubletten früh erkennen
- vor riskanten Aktionen eine Vorschau zeigen
- nützliche Metadaten beim Merge erhalten
- nichts blind löschen
- Bereinigung verständlich halten
- große Bibliotheken pflegbar machen

### Merge-Verhalten
Beim Zusammenführen von Dubletten soll LinkVault wichtige Daten erhalten, zum Beispiel:
- Favoriten
- Tags
- Collections
- Notizen
- bessere Metadaten
- Import-/Quellkontext

---

## Import-Philosophie

Import ist nicht einfach nur „Datei hochladen“.

Für LinkVault bedeutet Import:

- zuerst Vorschau
- Dubletten erkennen
- Konflikte sichtbar machen
- Herkunft erhalten
- Metadaten soweit möglich bewahren
- stille destruktive Ergebnisse vermeiden

HTML bleibt die gemeinsame Baseline.  
Reichere browserspezifische Formate können später als Anreicherung ergänzt werden.

---

## Selfhosting-Philosophie

LinkVault ist bewusst so gedacht, dass es für kleine self-hosted Installationen praktisch bleibt.

### Standardpfad
- leichtgewichtig
- SQLite-basiert
- mit einem Dienst realistisch betreibbar
- einfach zu sichern
- einfach wiederherzustellen
- einfach zu aktualisieren
- realistisch für Proxmox-Homelab-Nutzung

### Schwere optionale Funktionen
Schwerere Themen wie Archive Worker, Screenshot/PDF, Reader-Extraktion, AI-Helfer oder größere Service-Topologien sind spätere optionale Erweiterungen und keine Standardvoraussetzung.

---

## Tech-Stack

Aktueller Kern-Stack:

- Python
- SQLite
- SQLite FTS5
- eigenes Backend-Runtime-Modell
- Firefox Companion Extension
- Proxmox VE / Debian LXC Deployment-Pfad
- stdlib-orientierter Testansatz

---

## Projektstatus

LinkVault ist aktiv in Entwicklung.

Die technische Basis ist bereits stark bei:
- Bookmark-Speicherung
- Dedup-Logik
- Import-Vorschau
- Browser-Companion-Grundlagen
- Proxmox-Installationspfad
- Backup-, Restore- und Update-Workflows

Die größte verbleibende sichtbare Produktlücke ist aktuell noch die Klarheit der Haupt-UI/GUI bei:
- Navigation
- Favoriten
- Organisation
- Dublettenpflege
- alltäglichen Bookmark-Workflows

---

## Dokumentation

Wichtige Dokumente:

- `ROADMAP.md`
- `ROADMAP.en.md`
- `PROJECT_MEMORY.md`
- `docs/linkvault_statusanalyse.md`
- `PRODUCT_SPEC.md`
- `ARCHITECTURE.md`
- `RESEARCH_IMPACT.md`
- `UX_RESEARCH_IMPACT.md`
- `COMPANION_EXTENSION.md`
- `COMPANION_EXTENSION_UPDATE.md`
- `DUPLICATE_PREFLIGHT.md`
- `DEDUP_SORTING_CATEGORIZATION.md`
- `PROXMOX_COMMUNITY_SCRIPT.md`
- `BACKUP_RESTORE.md`
- `UPDATE.md`
- `HELPER.md`

---

## Entwicklungsprioritäten

Aktuell hoch priorisiert:

- bookmark-zentrierte Navigation
- Quick Add
- Favoriten-/Tags-/Listen-/Collections-Workflows
- Duplicate Center UX
- breitere Import-/Export-/Migrationsabdeckung
- stabile Browser-Roundtrips
- weitere Proxmox-Betriebsreife

Niedriger priorisiert:

- Reader-Modus
- archivlastige Flows
- Screenshot / PDF / Single-HTML
- AI-Zusammenfassungen
- schwere Multi-Service-Erweiterungen
- Enterprise-Provisioning

---

## Zielgruppe

LinkVault richtet sich besonders an Menschen, die wollen:

- self-hosting
- Kontrolle über ihre Bookmarks
- Browser-Migrationsunterstützung
- Dublettenbereinigung
- Favoriten-Verwaltung
- Proxmox-freundliches Deployment
- ein fokussiertes System, das praktisch bleibt

---

## Leitfrage

Für jede größere Entscheidung fragt LinkVault:

**Macht das das Produkt besser als self-hosted Plattform für Bookmarks, Favoriten, Organisation, Dublettenbereinigung, Import/Export und sync-nahe Workflows?**

Wenn die Antwort hauptsächlich lautet „es macht LinkVault mehr zu einem Reader- oder Archivprodukt“, dann ist die Richtung falsch.

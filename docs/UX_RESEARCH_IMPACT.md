# UX Research Impact

## Quelle

Diese Auswertung basiert auf der lokalen Sammlung
`UX-Research-Sammlung fuer LinkVault` vom 19.04.2026. Sie vergleicht
Karakeep, linkding, Linkwarden, LinkAce, Readeck, Shiori und
community-scripts.org aus UX-/UI-/GUI-Sicht.

Die wichtigste Wirkung auf LinkVault: Das Projekt braucht nicht nur mehr
Funktionen, sondern bessere Sichtbarkeit fuer Pflegeaufgaben. Speichern und
Suchen sind nur der Anfang; Aufraeumen, Zusammenfuehren, Priorisieren,
Synchronisieren und Wiederlesen muessen als eigene Wege sichtbar werden.

## UX-Produktformel

```text
linkding-Klarheit
+ Karakeep-Arbeitsoberflaeche
+ Linkwarden-Archiv- und Collection-Tiefe
+ Readeck-Lesemodus
+ LinkAce-Verwaltungskontrolle
+ Shiori-Betriebseinfachheit
+ community-scripts.org-Entdeckbarkeit
```

## Wichtigste Erkenntnisse

### 1. Dubletten brauchen eine sichtbare Zentrale

Viele Referenztools haben technische URL-Pruefungen oder Import-Schutz. Was
oft fehlt, ist eine gut sichtbare UX fuer taegliche Dublettenpflege.

Konsequenz fuer LinkVault:

- `Dubletten` sollte ein Hauptnavigationspunkt werden.
- Vor dem Speichern braucht LinkVault spaeter einen Duplicate-Preflight:
  vorhanden oeffnen, aktualisieren, Archivversion anhaengen, separat speichern
  oder spaeter pruefen.
- Merge muss immer Vorschau, Dry-Run, klare Gewinnerregel und Undo bekommen.

### 2. Quick Add muss leicht bleiben

linkding und LinkAce zeigen: schnelles Speichern ist entscheidend. Karakeep
und Linkwarden zeigen zugleich, dass Metadaten, Listen, Favoriten und Archive
beim Speichern hilfreich sind, solange sie nicht den Standardfluss ueberladen.

Konsequenz fuer LinkVault:

- Ein Quick-Add-Feld sollte dauerhaft leicht erreichbar sein.
- Der Standarddialog bleibt kurz: URL, Titel, Tags, Collections, Favorit/Pin.
- Erweiterte Optionen wie Archivmodus, Regeln oder Duplicate-Details werden
  stufenweise aufgeklappt.

### 3. Navigation muss Pflegeaufgaben abbilden

Die Sammlung empfiehlt eine klare Hauptnavigation:

- Inbox
- Favoriten
- Dubletten
- Listen oder Collections
- Tags
- Archiv
- Aktivitaet
- Einstellungen

Konsequenz fuer LinkVault:

- Die aktuelle MVP-Seite darf simpel bleiben, aber das Zielbild sollte eine
  linke Navigation mit direkten Pflegebereichen bekommen.
- `Inbox` wird der Ort fuer neue oder unsortierte Links.
- `Aktivitaet` zeigt spaeter Import, Merge, Bulk-Aktionen, Restore und Regeln.

### 4. Bulk-Aktionen sind Kern-UX, kein Nebenfeature

Die UX-Recherche bestaetigt den bisherigen Schritt: Bulk Actions sind fuer
echte Bookmark-Pflege notwendig.

Konsequenz fuer LinkVault:

- Bereits umgesetzt: Auswahl, Tags hinzufuegen/entfernen, Collections setzen,
  Favorit/Pin setzen und Loeschen.
- Spaeter ergaenzen: bulk archive, bulk export, bulk share, bulk merge und
  Status-Aenderungen.

### 5. Sync und Konflikte brauchen eigene Oberflaechen

Browser-Erweiterungen, Mobile Share, Floccus/WebDAV und API-Importe erzeugen
Konflikte: gleiche URL mit anderen Tags, Offline-Capture, veraenderte
Collections oder doppelte Ordner.

Konsequenz fuer LinkVault:

- API-Token sollten nicht nur technisch existieren, sondern in einem
  Sync-Setup-Assistenten sichtbar werden.
- Spaeter braucht es ein Conflict Center fuer Sync-, Import- und Merge-Faelle.
- Jeder Konflikt braucht eine begruendete Entscheidung, nicht nur
  `replace`/`keep`.

### 6. Archivierung muss als Erlebnis sichtbar sein

Linkwarden und Readeck zeigen, dass Archive nicht nur Backup-Dateien sind. Sie
beeinflussen Lesen, Wiederfinden und Vertrauen.

Konsequenz fuer LinkVault:

- Archivstatus wird ein sichtbares Feld je Bookmark.
- Spaetere Save-Optionen: URL only, Reader, Single-HTML, PDF/Screenshot.
- Archivassets muessen in Backup/Restore und Merge-Plan auftauchen.

### 7. Betrieb ist auch UX

community-scripts.org zeigt, wie stark klare Suche, Kategorien, Copy/Paste-
Befehle, Default/Advanced-Auswahl und Nachinstallationshinweise wirken.

Konsequenz fuer LinkVault:

- Proxmox-Installation muss nicht nur funktionieren, sondern klar erklaeren:
  URL, Setup-Token, Healthcheck, Logs, Backup, Update.
- Ein Post-Install Helper sollte spaeter Update, Logs, Status, Backup/Restore
  und Diagnose fuehren.

## Priorisierte UX-Folgen

1. **Navigation/Startseite ueberarbeiten**: Quick Add, Suche, Inbox,
   Favoriten, Dubletten und Bulk-Auswahl klarer trennen.
2. **URL-Check / Duplicate Preflight**: vor dem Speichern anzeigen, ob eine URL
   bereits existiert.
3. **Dedup-Dashboard ausbauen**: Gruppen, Gewinner, Merge-Plan und Dry-Run
   visuell bearbeitbar machen.
4. **Activity/Audit vorbereiten**: Import, Bulk, Merge, Delete, Restore und
   spaeter Regeln nachvollziehbar machen.
5. **API-Token + Sync-Setup**: Token nicht nur als Endpoint, sondern mit
   Test-Button und Status sichtbar machen.
6. **Archivstatus in der UI**: zuerst Statusfeld, spaeter Reader/Archivtabs.
7. **Post-Install Helper**: Proxmox-Nutzer durch Update, Logs, Backup/Restore
   und Healthcheck fuehren.

## Bewusste MVP-Grenze

Die UX-Sammlung enthaelt viele groessere Ideen wie Mobile Share, Browser-
Extension, Conflict Center, Reader Tabs, Archive Preview und Sync Wizard. Diese
sind wichtig, aber nicht alle sofort MVP. Fuer den aktuellen Python-MVP zaehlt:

- bestehende Pflegefunktionen stabilisieren,
- echte Proxmox-Backup/Restore-Laeufe nachweisen,
- URL-Check und Dedup-UX als naechste Produktdifferenzierung bauen.

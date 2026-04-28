# LinkVault Companion Extension

## Ziel

Die LinkVault Companion Extension soll Bookmarks direkt aus unterstützten Browsern nach LinkVault bringen und LinkVault-Bookmarks kontrolliert wieder in Browserstrukturen zurückführen.

Die Extension ist primär gedacht für:

- aktuellen Tab schnell speichern
- Browser-Bookmarks lesen
- Bookmark-Importe vorbereiten
- Import-Vorschauen anzeigen
- Duplikate und Konflikte vor dem Import sichtbar machen
- gefilterte LinkVault-Bookmarks exportieren
- sichere, nachvollziehbare Browser-Rückimporte ermöglichen

## Produktrolle

Die Companion Extension ist **kein eigenständiges Read-later-, Reader- oder Archiv-Frontend**.

Sie ist eine **Begleiterweiterung für Bookmark-Management, Import/Export und sync-nahe Workflows**.

### Kernzweck
Die Extension unterstützt LinkVault dabei, ein besseres System zu sein für:

- Bookmark-Erfassung
- Favoriten-/Link-Verwaltung
- Browser-Import
- Browser-Rückimport
- Duplikatprüfung
- Konfliktbewusste Synchronisationsvorbereitung

### Nicht-Ziele
Die Extension ist nicht primär gedacht für:
- Artikel lesen
- Archivansicht
- Reader-Modus
- Content-Consumption
- Passwort-/Cookie-/History-Zugriff
- vollautomatischen Zwei-Wege-Sync ohne Review

---

## Unterstützte Browser

Die Extension soll sich an Browsern orientieren, die WebExtension-/Chromium-kompatible Bookmark-Zugriffe erlauben.

Geplanter oder relevanter Scope:

- Firefox
- Chrome
- Edge
- Brave
- Vivaldi
- Opera

### Wichtig
Nicht jeder Browser bietet dieselben Bookmark-APIs, Metadaten oder Sync-Möglichkeiten.
Die Extension soll daher:
- defensiv mit Browserunterschieden umgehen
- nur verfügbare Felder voraussetzen
- fehlende Metadaten sauber behandeln
- LinkVault nicht von browser-spezifischen Sonderfällen abhängig machen

---

## Kernvoraussetzungen

LinkVault stellt API-Tokens für Import, Extension und Automatisierung bereit.

### Token-Regeln
- Tokens werden nur gehasht gespeichert
- Klartext wird nur einmal angezeigt
- Token-Verwaltung erfordert Browser-Login in LinkVault
- Tokens können für Extension-Zugriffe genutzt werden
- Tokens dürfen nicht eigenständig neue Tokens erzeugen oder löschen

### Verbindungsdaten
Die Extension speichert:
- LinkVault-URL
- API-Token
- ggf. lokale Statusdaten für den eigenen Arbeitsfluss

---

## Minimaler Kernumfang

Die erste sinnvolle Extension-Version muss vor allem diese Aufgaben gut lösen:

1. LinkVault-URL und API-Token speichern  
2. Verbindung zu LinkVault prüfen  
3. aktuellen Tab als Bookmark speichern  
4. Browser-Bookmark-Baum lesen  
5. Bookmark-Import-Vorschau an LinkVault senden  
6. Import nach Nutzerprüfung starten  
7. gefilterte LinkVault-Bookmarks exportieren  
8. sichere Browser-Rückimport-Vorschau ermöglichen

## Bewusst klein halten

Der Kernumfang soll bewusst **nicht** sofort enthalten:

- vollautomatischen Zwei-Wege-Sync
- automatisches Löschen bestehender Browser-Bookmarks
- Zugriff auf Passwörter
- Zugriff auf Browser-History als Standard
- Zugriff auf Formular-/Autofill-Daten
- Reader-/Archivfunktionen in der Extension selbst
- schwere lokale Profilanalyse ohne klare Nutzerentscheidung

---

## Haupt-Workflows

## 1. Aktuellen Tab speichern

Ein schneller Alltagsworkflow:

1. Nutzer öffnet die Extension
2. aktuelle LinkVault-Instanz wird erkannt oder aus gespeicherter URL genutzt
3. aktueller Tab wird gelesen
4. URL wird an LinkVault gesendet
5. LinkVault prüft Duplicate Preflight
6. Nutzer sieht Ergebnis:
   - neu speichern
   - vorhandenen Bookmark öffnen
   - vorhandenen Bookmark aktualisieren
   - bewusst separat speichern

### Ziel
Der einfachste Flow der Extension muss sich wie ein schneller Bookmark-Speicher anfühlen.

---

## 2. Browser-Bookmarks importieren

Die Extension soll Browser-Bookmarks lesen und strukturiert an LinkVault übergeben.

### Import-Schritte
1. Browser-Bookmark-Baum lesen
2. optional filtern
3. strukturierte Import-Vorschau an LinkVault senden
4. LinkVault prüft:
   - Struktur
   - Duplikate
   - Konflikte
   - Importplan
5. Nutzer entscheidet
6. Import wird durchgeführt

### Wichtige Metadaten
Sofern verfügbar, sollen mitgegeben werden:
- Titel
- URL
- Ordner / Root
- Ordnerpfad
- Position
- Browser-Bookmark-ID
- Quelle / Browser
- Zeitinformationen wie `dateAdded`, wenn vorhanden

---

## 3. Browser-Rückimport / Restore in den Browser

Die Extension darf einen sicheren Rückweg in den Browser bieten.

### Ziel
LinkVault-Bookmarks sollen kontrolliert in:
- neue Browser-Ordner
- bestehende Browser-Ordner
zurückgeschrieben werden können.

### Wichtige Regeln
- bestehende Browser-Links niemals blind löschen
- Dubletten sichtbar machen
- Konflikte vor Anwendung zeigen
- Auswahlmöglichkeiten anbieten
- Strukturpfade klar darstellen

### Erlaubte Entscheidungen
Je nach Fall:
- überspringen
- separat anlegen
- vorsichtig mergen
- aktualisieren
- in Zielordner verschieben, wenn explizit bestätigt

---

## API-Nutzung

### Healthcheck

```http
GET /healthz

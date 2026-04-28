# LinkVault Companion Extension Updates

## Ziel dieser Datei

Diese Datei beschreibt, wie die **LinkVault Companion Extension** während der Entwicklung, beim lokalen Testen und später bei der Verteilung aktualisiert werden soll.

Die Companion Extension ist eine Begleiterweiterung für:

- schnelles Speichern von Bookmarks
- Browser-Bookmark-Import
- gefilterten Export
- Duplicate-Preflight
- konfliktbewusste Import-/Rückimport-Flows
- sync-nahe, aber kontrollierte Bookmark-Workflows

Sie ist **nicht** primär gedacht für:

- Read-later-Funktionen
- Reader-Modus
- Archivkonsum
- selbständige Inhaltsplattform-Logik

---

## Grundprinzip

Während der Entwicklung soll die Extension **nicht jedes Mal entfernt und neu installiert** werden müssen.

Das bevorzugte Update-Modell ist:

- lokale Dateien ändern
- Extension im Browser **neu laden**
- weiter testen

Dadurch bleiben Entwicklung und Fehlersuche schnell und reproduzierbar.

---

## Entwicklungs-Update statt Neuinstallation

## Firefox

Bei einer lokal geladenen temporären Extension reicht normalerweise:

- `about:debugging`
- `This Firefox`
- `LinkVault Companion`
- `Reload`

## Chromium-basierte Browser

Bei einer entpackten Extension reicht normalerweise:

- Browser öffnen
- `Extensions`
- `Developer mode`
- `Reload`

## Wichtig
Die Extension soll möglichst **aus demselben lokalen Ordner** erneut geladen werden.

Wenn dieselbe lokale Installation nur neu geladen wird, bleiben gespeicherte Zustände oft erhalten oder verhalten sich zumindest stabiler als bei kompletter Neuinstallation.

---

## URL und API-Token beibehalten

Die Extension speichert lokale Verbindungsdaten wie:

- LinkVault-URL
- API-Token
- ggf. weitere lokale Einstellungswerte

Diese Daten liegen im lokalen Extension-Speicher des Browsers.

## Ziel
Bei einem normalen Reload sollen URL und Token **möglichst erhalten bleiben**, damit Entwickler und Nutzer nicht bei jeder kleinen Änderung neu konfigurieren müssen.

## Wichtige Bedingung
Das funktioniert am zuverlässigsten, wenn:

- die Extension dieselbe Identität behält
- derselbe lokale Ordner verwendet wird
- keine vollständige Entfernung erfolgt

## Wann Daten verloren gehen können
URL und Token können neu eingegeben werden müssen, wenn:

- die Extension vollständig entfernt wird
- sie aus einem anderen Ordner neu geladen wird
- die lokale Extension-Identität wechselt
- das Browser-Profil zurückgesetzt wurde

---

## Stabile lokale Identität

Für die Entwicklung ist eine stabile lokale Extension-Identität wichtig.

### Warum?
Sie hilft dabei:

- Reloads reproduzierbar zu machen
- lokale Daten stabiler zu halten
- Update-Tests realistischer zu machen
- weniger Reibung im Entwicklungsalltag zu erzeugen

### Ziel
Ein Reload soll sich wie ein **technisches Update derselben Extension** verhalten, nicht wie eine komplett neue Installation.

---

## Kein Selbstupdate über Ajax oder Remote-Code

Die Companion Extension soll **ihren eigenen Code nicht aus dem Netzwerk nachladen und selbst ersetzen**.

### Warum nicht?
Browser blockieren so etwas aus guten Gründen:

- Sicherheitsrisiko
- Umgehung von Review-/Signaturwegen
- unklare Herkunft von Code
- schwer nachvollziehbares Laufzeitverhalten

### Grundsatz
Die Extension darf nicht zu einem System werden, das sich heimlich selbst umbaut.

### Daher gilt
Keine dieser Strategien als Standardweg:

- Ajax-Selbstupdate
- dynamisches Nachladen von unkontrolliertem Code
- versteckte Remote-Code-Pfade
- automatischer Austausch der lokalen Extension-Dateien aus dem Web

---

## Sinnvolle Update-Wege

## 1. Entwicklung
Der Standardweg während der Entwicklung:

- lokale Dateien ändern
- Browser-Extension reloaden
- testen

Das ist der wichtigste und bevorzugte Weg im Alltag.

## 2. Spätere Paketverteilung
Für echte Nutzerverteilung sind später saubere Paketwege sinnvoll, zum Beispiel:

- signiertes Firefox-Addon
- gepackte Chromium-Extension
- kontrollierter Update-Kanal je Browsermodell

## 3. Optionale spätere Selfhost-/Homelab-Verteilung
Später möglich, aber nicht nötig für den Kern:

- eigener Update-Mechanismus über signierte Pakete
- eigener Manifest-/Release-Pfad
- kontrollierte interne Verteilung für Homelab/Enterprise-ähnliche Setups

### Bedingung
Auch dabei gilt:
- keine unkontrollierten Selbstupdates
- keine Reader-/Archiv-Zweckentfremdung
- Fokus bleibt auf Bookmark-/Import-/Export-/Duplicate-/Sync-Hilfe

---

## Praktischer Entwickler-Workflow

## LinkVault-Server aktualisieren
Wenn LinkVault im LXC aktualisiert wurde, reicht es normalerweise danach, die Extension im Browser neu zu laden.

Beispiel für den Server:

```bash id="fj2g1v"
pct exec 112 -- linkvault-helper update

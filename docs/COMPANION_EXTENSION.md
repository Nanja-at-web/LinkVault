# LinkVault Companion Extension Plan

## Ziel

Die Companion Extension soll Bookmarks direkt aus Firefox, Chrome, Edge, Brave,
Vivaldi und Opera nach LinkVault senden, ohne dass Nutzer HTML oder JSON
manuell kopieren muessen.

## Core-Voraussetzung

LinkVault hat API-Token fuer Import, Extension und Automatisierung:

- Token werden nur gehasht in SQLite gespeichert.
- Der Klartext wird nur einmal beim Erstellen angezeigt.
- Requests koennen `Authorization: Bearer <token>` oder
  `X-LinkVault-Token: <token>` nutzen.
- Token-Verwaltung liegt im Tab `Betrieb`.
- Token-Verwaltung selbst braucht weiterhin Browser-Login, damit ein Token
  nicht neue Token erzeugen oder entfernen kann.

## Erste Extension-Version

Minimaler Scope:

- LinkVault-URL und API-Token speichern.
- Aktuellen Tab als Bookmark speichern.
- Browser-Bookmarks lesen und als Import-Vorschau an LinkVault senden.
- Danach Import starten.

Nochmal bewusst klein:

- kein Zwei-Wege-Sync
- kein automatisches Loeschen
- kein Zugriff auf Passwoerter, History oder Formulardaten
- keine Cloud-Anbindung

## API-Nutzung

Healthcheck:

```http
GET /healthz
```

Discovery/Fingerprinting:

```http
GET /.well-known/linkvault
```

```json
{
  "app": "LinkVault",
  "version": "0.1.0",
  "health": "/healthz"
}
```

Bookmark speichern:

```http
POST /api/bookmarks
Authorization: Bearer lv_pat_...
Content-Type: application/json

{
  "url": "https://example.com",
  "title": "Example",
  "tags": ["browser"],
  "collections": ["Inbox"]
}
```

Import-Vorschau:

```http
POST /api/import/browser-bookmarks/preview
Authorization: Bearer lv_pat_...
Content-Type: application/json

{
  "items": [
    {
      "url": "https://example.com",
      "title": "Example",
      "collections": ["Bookmarks Toolbar", "Dev"],
      "source_browser": "firefox-extension",
      "source_root": "Bookmarks Toolbar",
      "source_folder_path": "Bookmarks Toolbar / Dev",
      "source_position": 4,
      "source_bookmark_id": "abc123"
    }
  ]
}
```

Chromium-JSON-Vorschau:

```http
POST /api/import/chromium-json/preview
Authorization: Bearer lv_pat_...
Content-Type: application/json

{
  "data": "{\"roots\":{...}}"
}
```

## Browser-Realitaet

Firefox' interne Funktion "Daten aus anderem Browser importieren" kann
LinkVault nicht direkt nutzen. Eine Web-App darf nicht auf lokale
Browserprofile oder andere Browserdaten zugreifen. Eine Extension darf mit
passender Berechtigung aber Bookmarks lesen und an LinkVault senden.

Darum ist der realistische Weg:

1. API-Token im LinkVault-Core.
2. Browser-Extension mit `bookmarks`-Berechtigung.
3. Import-Vorschau in LinkVault.
4. Erst spaeter optional Native Messaging fuer lokale Profil-/Datei-Importe.

## Entwickler-Preview

Die erste Extension-Version liegt unter:

```text
extensions/linkvault-companion/
```

Sie kann lokal als temporaere Firefox-Extension oder als entpackte
Chromium-Extension geladen werden.

Fuer Updates in der Entwickler-Preview soll die Extension nicht jedes Mal
entfernt werden. Stattdessen im Browser `Reload` fuer die temporaere bzw.
entpackte Extension ausfuehren. Die Firefox-ID
`linkvault-companion@nanja-at-web.local` ist im Manifest fest eingetragen,
damit URL und API-Token beim Reload normalerweise erhalten bleiben. Details:
[Companion Extension Updates](COMPANION_EXTENSION_UPDATE.md).

Aktueller Funktionsumfang:

- LinkVault-URL und API-Token speichern.
- LinkVault-Server ueber aktuelle Eingabe, gespeicherte URL, offene Tabs,
  `linkvault.local`, `linkvault` und optionalen Subnetzscan suchen.
- Verbindung gegen `/healthz` und `/api/bookmarks` testen.
- aktuellen Tab als Bookmark speichern.
- Browser-Bookmark-Baum ueber die WebExtensions-`bookmarks`-API lesen.
- Alle Browser-Bookmarks oder einen einzelnen Browser-Ordner fuer
  Vorschau/Import auswaehlen.
- Browser-Bookmarks vor Vorschau/Import nach Ordner, Textsuche,
  Adresse/Domain und hinzugefuegt-Datum filtern.
- Browser-Struktur beim Import erhalten: Quelle, Root, Ordnerpfad, Position
  und Browser-Bookmark-ID werden als Metadaten in LinkVault gespeichert.
- Import-Vorschau an LinkVault senden und erste Detailzeilen im Popup zeigen.
- Browser-Bookmarks nach LinkVault importieren.
- LinkVault-Bookmarks wieder in den Browser importieren: mit Vorschau, Zielwahl
  zwischen neuem Restore-Ordner und bestehendem Browser-Ordner, LinkVault-
  Exportfiltern und Duplikatstrategie.
- Beim Browser-Rueckimport werden bestehende Links nie geloescht. Duplikate
  koennen uebersprungen, vorsichtig gemerged oder aktualisiert und in den
  Zielordner verschoben werden.
- Interne Browser-URLs wie `about:`, `place:` oder `moz-extension:` werden
  uebersprungen, weil LinkVault normale HTTP/HTTPS-Bookmarks speichert.

Die Extension sendet fuer den Browser-Baum strukturierte JSON-Daten an
LinkVault, damit Ordnerpfad und Reihenfolge fuer spaetere Restore-/Sync-
Workflows erhalten bleiben:

- `POST /api/import/browser-bookmarks/preview`
- `POST /api/import/browser-bookmarks`

Der erste sichere Rueckweg in den Browser nutzt:

- `GET /api/export/browser-bookmarks`

Der Endpoint unterstuetzt dieselben einfachen Filter wie die Bookmark-Liste:
`q`, `favorite`, `pinned`, `domain`, `tag`, `collection` und `status`.

Die Extension erstellt daraus zuerst eine Restore-Vorschau. Danach kann sie:

- einen neuen Ordner wie `LinkVault Restore ...` anlegen,
- einen bestehenden Browser-Ordner als Ziel nutzen,
- vorhandene Links ueberspringen,
- vorhandene Links ohne Verschieben aktualisieren,
- vorhandene Links aktualisieren und in den Zielordner verschieben.

Ein destruktiver Zwei-Wege-Sync mit Loeschungen bleibt bewusst offen und
braucht spaeter eine eigene Konfliktvorschau mit klarer Warnung.

Der klassische Netscape-HTML-Import bleibt fuer Dateiimporte und als
Kompatibilitaetsformat im LinkVault-Core erhalten.

Die Ordnerauswahl importiert den gewaehlten Ordner inklusive Unterordnern.
Eine feinere Einzel-Link-Auswahl ist als naechster Schritt sinnvoll, sobald
der Ordner-Import in Firefox und Chromium stabil getestet ist.

Dateibasierte Browser-Exporte laufen nicht ueber die Extension, sondern ueber
den LinkVault-Import-Tab. Dort sind Browser-HTML, Chromium-JSON, Firefox-JSON
und Safari-ZIP mit `Bookmarks.html` die ersten unterstuetzten Formate.

## Filtermodell

Die Extension soll sich an vertrauten Browser-Bibliotheken orientieren:
Ordnerbaum, Suche, Detailvorschau und bewusst ausgewaehlte Imports statt
blindem Komplettimport.

Sinnvolle Standardfilter:

- Ordner/Quelle aus dem Browser-Bookmark-Baum.
- Textsuche ueber Titel, URL und Ordnerpfad.
- Adresse oder Domain.
- Hinzugefuegt-Datum, soweit `dateAdded` verfuegbar ist.
- Interne Dubletten im Browser-Baum.
- Bereits in LinkVault vorhandene URLs.

Tags sind browseruebergreifend nicht verlaesslich ueber die WebExtensions-API
verfuegbar. Wenn ein Dateiimport Tags enthaelt, sollte LinkVault sie
uebernehmen. Die Extension sollte Tags aber nicht als Pflichtfilter fuer alle
Browser behandeln.

`Zuletzt besucht` und `Meistbesucht` brauchen Browser-History-Zugriff. Das
soll spaeter nur als optionales `History-Enrichment` kommen, mit expliziter
`history`-Berechtigung und klarer Nutzerentscheidung. Standard bleibt:
Bookmarks ja, Passwoerter/Autofill/Cookies/History nein.

## Naechste Umsetzungsschritte

- Node.js nur fuer lokale/CI-Entwicklungschecks einplanen, damit
  `node --check extensions/linkvault-companion/*.js` laufen kann. Node bleibt
  keine Runtime-Abhaengigkeit fuer LinkVault oder den Proxmox-LXC.
- Discovery-Ergebnis spaeter mit Servername/Hostname und HTTPS-Hinweis
  anreichern.
- Bessere Vorschau in der Extension mit Detailzeilen statt nur Zaehlern.
- Einzelne Links innerhalb eines Ordners vor dem Import auswaehlen.
- Filtervorschau mit Trefferzahl direkt vor dem Senden an LinkVault.
- Duplicate-Entscheidung fuer aktuellen Tab direkt in der Extension anzeigen.
- Konfliktvorschau fuer spaeteren echten Browser-Restore/Sync bauen.
- Optionales History-Enrichment fuer zuletzt besucht und meistbesucht pruefen.
- Paketierung fuer Firefox/Chromium vorbereiten.
- Versionsabgleich zwischen LinkVault-Server und Companion Extension anzeigen.

## Fehlersuche

Wenn `Test connection` in der Extension fehlschlaegt:

1. `http://LINKVAULT-IP:3080/healthz` in einem normalen Browser-Tab oeffnen.
   Dort muss JSON mit `"ok": true` erscheinen.
2. LinkVault im LXC aktualisieren, damit CORS/OPTIONS-Unterstuetzung aktiv ist.
3. Temporaere Extension nach Code-Aenderungen im Browser neu laden. Entfernen
   ist nur noetig, wenn Berechtigungen oder die lokale Installation haengen.
4. Wenn Firefox nach Host-/Netzwerkberechtigung fragt, Zugriff auf den
   LinkVault-Host erlauben.
5. API-Token komplett neu kopieren und pruefen, ob er unter `Betrieb` noch
   existiert.
6. Wenn `/healthz` im normalen Tab nicht erreichbar ist, liegt es an IP,
   Netzwerk, Containerstatus oder Firewall, nicht an der Extension.

LinkVault laeuft im Homelab/LXC-Standard bewusst per HTTP. Die Extension
erlaubt deshalb HTTP-Verbindungen zu lokalen/selfhosted LinkVault-Instanzen
explizit im Manifest. Wenn Firefox in den Entwicklerwerkzeugen meldet, dass
`http://.../healthz` auf `https://.../healthz` hochgestuft wird, ist noch eine
alte temporaere Extension-Version geladen. Dann zuerst die Extension im Browser
neu laden. Wenn das nicht reicht, einmal entfernen und wieder ueber
`extensions/linkvault-companion/manifest.json` laden.

Firefox verlangt, dass die Berechtigungsabfrage direkt aus dem Button-Klick
kommt. Wenn Berechtigungsfehler nach einem Reload bleiben, temporaeres Add-on
einmal entfernen und neu ueber `manifest.json` laden.

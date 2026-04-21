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
POST /api/import/browser-html/preview
Authorization: Bearer lv_pat_...
Content-Type: application/json

{
  "data": "<!DOCTYPE NETSCAPE-Bookmark-file-1>..."
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

Aktueller Funktionsumfang:

- LinkVault-URL und API-Token speichern.
- Verbindung gegen `/healthz` und `/api/bookmarks` testen.
- aktuellen Tab als Bookmark speichern.
- Browser-Bookmark-Baum ueber die WebExtensions-`bookmarks`-API lesen.
- Alle Browser-Bookmarks oder einen einzelnen Browser-Ordner fuer
  Vorschau/Import auswaehlen.
- Import-Vorschau an LinkVault senden und erste Detailzeilen im Popup zeigen.
- Browser-Bookmarks nach LinkVault importieren.
- Interne Browser-URLs wie `about:`, `place:` oder `moz-extension:` werden
  uebersprungen, weil LinkVault normale HTTP/HTTPS-Bookmarks speichert.

Die Extension erzeugt fuer den Bookmark-Baum intern Netscape-HTML und nutzt
die vorhandenen LinkVault-Endpunkte:

- `POST /api/import/browser-html/preview`
- `POST /api/import/browser-html`

Die Ordnerauswahl importiert den gewaehlten Ordner inklusive Unterordnern.
Eine feinere Einzel-Link-Auswahl ist als naechster Schritt sinnvoll, sobald
der Ordner-Import in Firefox und Chromium stabil getestet ist.

Dateibasierte Browser-Exporte laufen nicht ueber die Extension, sondern ueber
den LinkVault-Import-Tab. Dort sind Browser-HTML, Chromium-JSON, Firefox-JSON
und Safari-ZIP mit `Bookmarks.html` die ersten unterstuetzten Formate.

## Naechste Umsetzungsschritte

- Bessere Vorschau in der Extension mit Detailzeilen statt nur Zaehlern.
- Einzelne Links innerhalb eines Ordners vor dem Import auswaehlen.
- Duplicate-Entscheidung fuer aktuellen Tab direkt in der Extension anzeigen.
- Paketierung fuer Firefox/Chromium vorbereiten.

## Fehlersuche

Wenn `Test connection` in der Extension fehlschlaegt:

1. `http://LINKVAULT-IP:3080/healthz` in einem normalen Browser-Tab oeffnen.
   Dort muss JSON mit `"ok": true` erscheinen.
2. LinkVault im LXC aktualisieren, damit CORS/OPTIONS-Unterstuetzung aktiv ist.
3. Temporaere Extension nach Code-Aenderungen entfernen und neu laden.
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
alte temporaere Extension-Version geladen. Dann die temporaere Extension
entfernen und neu ueber `extensions/linkvault-companion/manifest.json` laden.

Firefox verlangt, dass die Berechtigungsabfrage direkt aus dem Button-Klick
kommt. Wenn Berechtigungsfehler nach einem Update bleiben, temporaeres Add-on
entfernen und neu ueber `manifest.json` laden.

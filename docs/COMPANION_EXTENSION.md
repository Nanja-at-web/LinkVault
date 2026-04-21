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

## Naechste Umsetzungsschritte

- Manifest-V3 Extension-Skeleton fuer Chromium und Firefox vorbereiten.
- Einstellungsseite fuer LinkVault-URL und API-Token bauen.
- Verbindungstest gegen `/healthz`.
- Aktuellen Tab speichern.
- Browser-Bookmark-Baum lesen und als Importdaten an LinkVault senden.
- Vorschau- und Import-Flow in der Extension anzeigen.

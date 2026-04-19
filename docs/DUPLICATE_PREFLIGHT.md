# Duplicate Preflight

## Ziel

Beim Speichern einer URL prueft LinkVault jetzt vorab, ob diese URL bereits
vorhanden ist oder sehr wahrscheinlich zu einem bestehenden Bookmark gehoert.

Der Preflight unterscheidet:

- `exact_url`: exakt dieselbe URL wurde bereits gespeichert,
- `normalized_url`: die normalisierte URL existiert bereits, zum Beispiel ohne
  Tracking-Parameter,
- `similar_url`: eine aehnliche URL auf derselben Domain existiert bereits.

## API

Normales Speichern ist serverseitig geschuetzt. Wenn ein Treffer gefunden wird,
antwortet `POST /api/bookmarks` mit `409 Conflict` und dem Preflight-Ergebnis.

Bewusstes doppeltes Speichern ist nur mit `allow_duplicate: true` moeglich.

```bash
curl -X POST http://127.0.0.1:3080/api/bookmarks/preflight \
  -H 'content-type: application/json' \
  -d '{"url":"https://example.com/docs?utm_source=news"}'
```

Antwort:

```json
{
  "has_matches": true,
  "normalized_url": "https://example.com/docs",
  "matches": [
    {
      "match_type": "normalized_url",
      "score": 95,
      "reason": "Normalized URL already exists",
      "bookmark": {}
    }
  ]
}
```

## UI-Verhalten

Beim Speichern zeigt LinkVault Treffer direkt unter dem Formular. Nutzer koennen:

- den vorhandenen Bookmark oeffnen,
- den vorhandenen Bookmark mit den Formularfeldern aktualisieren,
- bewusst trotzdem einen neuen Bookmark speichern.

Es wird noch kein Merge ausgefuehrt und nichts geloescht. Ohne ausdrueckliche
Nutzeraktion speichert die API keine Dublette.

## Dedup-Dashboard

Der Dry-Run zeigt nun:

- Dublettengruppen,
- Gewinner-Vorschlag,
- Feldunterschiede fuer URL, Titel, Beschreibung, Tags, Collections, Notizen,
  Favorite und Pin,
- Merge-Plan ohne Loeschung.

## Noch offen

- Archivversionen spaeter in Preflight-Entscheidungen einbeziehen.
- Import-Preflight fuer Browser-HTML und Tool-Migrationen ergaenzen.
- Destruktionsfreien Merge mit Undo vorbereiten.

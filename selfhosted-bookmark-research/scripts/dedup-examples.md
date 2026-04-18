# Dedup-Beispiele

## Karakeep – API-orientierter Pseudocode

```bash
# 1. Alle Bookmarks aus API lesen
# 2. URL kanonisieren
# 3. Gruppen mit gleicher URL bilden
# 4. Sieger behalten (z.B. favorisiert > mit Highlights > älter)
# 5. Tags/Listen/Notizen auf Sieger mergen
# 6. Dubletten löschen
```

## linkding – Beispiel (vereinfacht)

```python
import requests
from urllib.parse import urlsplit, urlunsplit

def canon(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, parts.query, ""))

# Dann: Bookmarks laden, nach canon(url) gruppieren, Sieger bestimmen, Dubletten löschen
```

## Linkwarden – konservativer Ansatz

```bash
# 1. Export erzeugen
# 2. URLs pro Collection/Subcollection normalisieren
# 3. Gepinnte Links bevorzugen
# 4. Archive-Dateien nicht verwaisen lassen
# 5. Löschläufe erst simulieren
```

## LinkAce – Export/Reimport-Ansatz

```bash
# 1. HTML oder CSV exportieren
# 2. extern deduplizieren
# 3. in Testinstanz importieren
# 4. Import Queue beobachten
```

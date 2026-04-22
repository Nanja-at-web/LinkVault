# Demo-UX-Analyse Impact

Stand: 2026-04-22

Die Demo-UX-Analyse vergleicht Linkwarden, linkding und Karakeep. Fuer
LinkVault ist die wichtigste Ableitung: LinkVault sollte nicht nur Funktionen
anhaeufen, sondern die Arbeitswege sichtbar und schnell bedienbar machen.

## Produktlinien Aus Dem Vergleich

| Referenz | Staerke | Konsequenz Fuer LinkVault |
| --- | --- | --- |
| Linkwarden | Dashboard, Collections, Pinning, klare Objektkarten | Inbox, Favoriten, Pins und Collections bleiben sichtbare Navigationsziele. |
| linkding | Minimalismus, schnelle Suche, Tastatursteuerung | Suche muss jederzeit erreichbar sein; Shortcuts werden frueh eingefuehrt. |
| Karakeep | Workspace mit Listen, Archiv, Preview, Favourites | Organisation, Preview und spaetere Archivfunktionen bekommen eigene Bereiche. |

## Direkt Uebernommene Punkte

- Tastaturkuerzel fuer zentrale Wege:
  - `Ctrl/Cmd+K`: Bookmarks oeffnen und Suche fokussieren.
  - `N`: Speichern oeffnen und URL-Feld fokussieren.
  - `I`: Import oeffnen.
  - `D`: Dubletten oeffnen und Dry-Run aktualisieren.
  - `B`: Bookmarks oeffnen.
- Shortcuts werden in der UI sichtbar erklaert.
- Dubletten bleiben ein eigener Workflow, nicht nur eine Fehlermeldung beim
  Speichern.

## Naechste UX-Schritte

- Seitenstruktur weiter Richtung Sidebar/Workspace entwickeln:
  Inbox, Favoriten, Pins, Tags, Collections, Dubletten, Import, Betrieb.
- Eine kompakte Bookmark-Liste mit Preview-Panel pruefen.
- Unterschiede zwischen Favorit und Pin in Microcopy und UI deutlicher machen.
- Import-Assistent weiter ausbauen: Quelle, Format, Vorschau, Konflikte und
  Ergebnisbericht.
- Accessibility-Pruefung: Landmarken, Fokusreihenfolge, Kontrast und
  Screenreader-Statusmeldungen.

## Bewusste Abgrenzung

LinkVault bleibt im Core leichtgewichtig. Linkwarden- und Karakeep-artige
Archiv- und Preview-Funktionen sollen optional wachsen, waehrend linkding-artige
Schnelligkeit und Bedienbarkeit im MVP schon spuerbar sein sollen.

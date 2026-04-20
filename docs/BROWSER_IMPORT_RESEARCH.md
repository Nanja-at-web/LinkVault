# Browser- und Import-Research Impact

## Quelle

Diese Auswertung basiert auf den lokalen Anhaengen vom 20.04.2026:

- `LinkVault Forschungs-Paket fuer Selfhosted Bookmark- und Archiv-Apps`
- `LinkVault Browser API Research Bundle`

Die erste Sammlung erweitert den Tool-Vergleich von Karakeep, linkding,
Linkwarden, LinkAce, Readeck und Shiori um Omnivore, Betula, Grimoire,
Shaarli und Wallabag. Die zweite Sammlung vergleicht Browser-Importe,
Bookmark-APIs, Sync-Verhalten und Metadatenformate fuer Chrome/Chromium,
Firefox, Edge, Safari, Brave, Vivaldi, Opera, Samsung Internet, DuckDuckGo
Browser und Tor Browser.

## Wichtigste Wirkung Auf LinkVault

Die neuen Daten bestaetigen LinkVaults Kernrichtung, verschieben aber die
Import-Architektur nach vorne. LinkVault sollte nicht nur
`Browser-Bookmark-HTML` importieren, sondern ein verlustarmes Importmodell
bekommen:

```text
Netscape-HTML als Baseline
+ optionale Vendor-Enrichment-Parser
+ kanonisches internes Import-Schema
+ Rohdaten-Erhaltung fuer unbekannte Felder
+ nicht-destruktive Konflikt- und Merge-Workflows
```

HTML bleibt der einzige wirklich breite Austauschstandard. Gleichzeitig ist
HTML verlustbehaftet: Browser-GUIDs, `dateLastUsed`, interne Flags,
Reading-List-Zustand, Speed-Dial-Zustand, Sync-Herkunft und manche Tags gehen
je nach Browser verloren. LinkVault sollte deshalb HTML akzeptieren, aber
Chromium-JSON, Firefox-JSON/JSONLZ4 und Safari-ZIP spaeter als optionale
Anreicherungsquellen behandeln.

## Vergleich Der Browser-Familien

| Familie | LinkVault-Folge |
|---|---|
| Chrome/Chromium, Edge, Brave, Vivaldi, Opera | Eine gemeinsame Chromium-Importfamilie planen, aber Browser-spezifische Felder wie Speed Dial, Reading List, Collections/Favorites und Extension-Sync nicht blind gleichsetzen. |
| Firefox und Tor Desktop | HTML plus JSON/JSONLZ4 als reichere Quelle fuer GUIDs, Folder-Struktur, Zeitstempel und teils Tags behandeln. Tor Android nicht als vollwertigen Exportpfad voraussetzen. |
| Safari | ZIP-Import mit `Bookmarks.html` und Metadaten vorbereiten; Reading List als eigenes Konzept behandeln. Safari Web Extensions nicht als verlaesslichen Bookmark-Automation-Weg einplanen. |
| Samsung Internet und DuckDuckGo Browser | Zunaechst als eingeschraenkte Import-/Sync-Quellen behandeln; keine Bookmark-API voraussetzen. |

## Kanonisches Import-Schema

LinkVault sollte langfristig neben dem normalen Bookmark-Datensatz eine
Import-Schicht halten. Wichtige Felder:

- Quelle: `source_browser`, `source_profile`, `source_device`,
  `source_format`, `source_file_checksum_sha256`.
- Browser-Identitaet: `source_id`, `source_guid`, `parent_source_id`,
  `source_path`.
- URL-Felder: `url_raw`, `url_normalized`, `canonical_url_hash`.
- Zeitstempel: `added_at`, `modified_at`, `last_used_at`, `imported_at`.
- Struktur: `folder_path`, `is_folder`, `is_bookmark`, `is_separator`.
- Semantik: `is_favorite`, `is_reading_list`, `is_speed_dial`,
  `is_mobile_root`, `is_managed`.
- Inhalt: `tags`, `notes`, `nickname`, `description`, `annotations`.
- Privacy: `icon_download_policy`, `privacy_risk_flags`.
- Herkunft: `sync_origin`.
- Erhaltung: `raw_vendor_payload`.

Das ist bewusst groesser als der aktuelle MVP. Fuer den MVP reicht eine
kleinere Teilmenge, aber die Datenbank sollte so wachsen, dass spaetere
Importer keine wertvollen Vendor-Felder verlieren.

## Folgen Fuer Dedup Und Merge

Die neuen Research-Daten stuetzen den aktuellen nicht-destruktiven Merge:

- Merges sollen Gewinner aktualisieren und Verlierer markieren, nicht sofort
  loeschen.
- Importquellen, Browser-GUIDs, Folder-Pfade, Tags, Notizen, Favoriten,
  Reading-List-Flags und Archivassets muessen in Merge-Plaenen sichtbar
  bleiben.
- Sync-Importe duerfen nicht als "sicherer Backup-Stand" gelten, weil mehrere
  Browser Sync eher als Merge-System statt als Backup beschreiben.
- Vor groesseren Importen braucht LinkVault eine Import-Vorschau mit
  Duplikatbericht, Konflikten, Gewinner-Vorschlag und Snapshot.

## Folgen Fuer Privacy

Browserdaten enthalten mehr als Links. Safari-ZIP-Exporte koennen
unverschluesselte Zusatzdaten enthalten; Favicons koennen beim Nachladen
Tracking- oder Netzwerkspuren erzeugen; Extension-Storage kann persoenliche
Einstellungen enthalten.

Konsequenz:

- Remote-Favicon-Nachladen sollte spaeter konfigurierbar sein.
- Importierte Rohdaten muessen lokal bleiben und duerfen nicht automatisch an
  AI-Provider oder externe Metadaten-Services gehen.
- Importprotokolle sollen zeigen, welche Quelle, welches Profil und welches
  Format verarbeitet wurden.

## Produktentscheidungen

1. Browser-HTML bleibt der erste Importpfad.
2. Danach kommt eine Import-Vorschau mit Dry-Run, Duplikatbericht und
   Konfliktliste.
3. Danach sollten Chromium-JSON, Firefox-JSON/JSONLZ4 und Safari-ZIP als
   Enrichment-Importer geplant werden.
4. API-Token sind vor Browser-Extension- und Mobile-Share-Flows wichtig.
5. Browser-Sync wird nicht als erstes als Zwei-Wege-Sync gebaut, sondern erst
   als nachvollziehbarer Import-/Export-/Konfliktworkflow.
6. Archive, Highlights und Browser-Metadaten muessen in Merge- und
   Backup/Restore-Planung mitgedacht werden.

## Naechste Konkrete Schritte

- Import-Vorschau fuer Browser-HTML bauen: Anzahl Links, Ordnerpfade,
  Duplikate, neue Tags/Collections, moegliche Konflikte.
- Import-Session-Tabelle einfuehren: Quelle, Datei, Checksumme, Zeitpunkt,
  Ergebniszahlen.
- Bookmark-Modell um Import-Herkunft und optionalen `raw_vendor_payload`
  vorbereiten.
- API-Token fuer Extension/Importer ergaenzen.
- Danach Chromium-/Firefox-/Safari-spezifische Parser als optionale Module
  planen.

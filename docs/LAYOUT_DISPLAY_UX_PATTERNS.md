# Layout And Display UX Patterns

Datum: 2026-04-22

Diese Notiz wertet die gezeigten Oberflaechen von Karakeep, Linkwarden und
linkding aus und gleicht sie mit den oeffentlichen Dokumentationen ab. Ziel:
LinkVault soll spaeter vertraute Ansichten anbieten, ohne den Core-MVP mit
schweren Archiv- oder Dashboard-Funktionen zu ueberladen.

## Quellen

- Karakeep Docs: https://docs.karakeep.app/using-karakeep/bookmarking
- Linkwarden Dashboard Docs: https://docs.linkwarden.app/Usage/dashboard
- Linkwarden Overview Docs: https://docs.linkwarden.app/Usage/overview
- Linkwarden Links Docs: https://docs.linkwarden.app/Usage/links
- linkding Website/Features: https://linkding.link/
- linkding Search Docs: https://linkding.link/search/
- linkding API Docs: https://linkding.link/api/

## Beobachtete Muster

### Karakeep

Karakeep ist visuell stark und behandelt Bookmarks als verschiedene
Objekttypen: Links, Texte/Notizen und Medien. Die Dokumentation beschreibt
Favoriten, Archiv, Notes, Highlights und Attachments als wichtige
Arbeitsbereiche. Listen sind die zentrale Organisationsebene, inklusive
manueller Listen und Smart Lists. Tags bleiben leichtgewichtige Labels fuer
Discovery und Filter.

Aus den Bildern:

- Layout-Menue mit Masonry, Grid, List und Compact.
- Spaltensteuerung fuer visuelle Layouts.
- Anzeigeoptionen fuer Notes, Tags und Titel.
- Bildoptionen fuer Cover/Fill oder Contain/Fit.
- Sidebar mit Home, Search, Tags, Highlights, Archive und Lists.
- Favoriten als eigener Arbeitsbereich.

Staerke fuer LinkVault: gute visuelle Durchsicht, Favoriten/Listen/Archiv
fuehlen sich wie echte Arbeitsraeume an.

Risiko fuer LinkVault: Masonry und grosse Previews brauchen stabile
Preview-/Archivdaten. Als Default waere das fuer den jetzigen MVP zu schwer.

### Linkwarden

Linkwarden positioniert Links, Collections und Tags als Kernobjekte. Die
Dokumentation beschreibt das Dashboard als persoenlichen Ueberblick ueber
Links, Collections und Tags; Links koennen gepinnt werden. Collections sind
folder-aehnlich und teilbar, waehrend Tags mehrere Keywords pro Link erlauben.
Die Preservation-Orientierung ist stark: Linkwarden speichert Inhalte fuer
spaetere Verfuegbarkeit.

Aus den Bildern:

- Dashboard mit konfigurierbaren Modulen.
- Edit-Layout-Menue, um Dashboard-Bereiche ein- oder auszublenden.
- Display-Menue fuer Link, Name, Image, Icon, Collection, Preserved Formats
  und Date.
- Sidebar fuer Dashboard, Links, Pinned, Collections und Tags.
- Kartenansicht mit Preview, Collection, Datum und Archiv-/Formatstatus.

Staerke fuer LinkVault: anpassbares Dashboard und Anzeigeoptionen helfen,
verschiedene Nutzungsarten sichtbar zu machen.

Risiko fuer LinkVault: ein Dashboard vor stabilen Datenfluesse kann schnell
kosmetisch werden. LinkVault sollte zuerst die Bookmark-Arbeitsliste stark
machen, dann Dashboard-Module ergaenzen.

### linkding

linkding ist listen- und pflegeorientiert. Die offizielle Beschreibung betont
minimal, schnell, gut lesbar, Tags, Bulk-Editing, Markdown-Notizen,
Read-it-later, Metadaten, Archivierung, Import/Export, Browser-Erweiterungen
und REST-API.

Aus den Bildern:

- Dichte Bookmark-Liste als Hauptansicht.
- Suchfeld direkt sichtbar.
- Sortier-/Filter-Popover mit Sort by, Shared filter, Unread filter.
- Apply und Save as default.
- Zeilenaktionen wie View, Edit, Archive, Remove und Notes.
- Seitenbereiche fuer Bundles und Tags.

Staerke fuer LinkVault: sehr geeignet fuer Pflege, Importkontrolle,
Dublettenbereinigung und grosse Bookmark-Mengen.

Risiko fuer LinkVault: weniger visuelles Browsing, wenn Nutzer viele
Preview-/Archivlinks betrachten wollen.

## LinkVault-Entscheidung

LinkVault sollte nicht nur eine einzige Ansicht haben. Die wichtige
Produktentscheidung ist:

- Standard bleibt schnell, kompakt und LXC-freundlich.
- Die Bookmark-Liste wird zuerst stark: Suche, Filter, Sortierung,
  Bulk-Aktionen, Dublettenstatus, Importstatus.
- Visuelle Layouts kommen als Umschalter, nicht als Pflicht.
- Masonry kommt erst nach stabilen Preview-Bildern und Archive-Worker.
- Anzeigeoptionen muessen pro Nutzer speicherbar sein.

Empfohlene Ansichten:

- Compact List: Standard fuer Inbox, Pflege und Dublettenarbeit.
- Detailed List: mehr Metadaten, Notes, Tags und Collections.
- Grid/Card: fuer visuelles Browsing mit Preview, Favicon und Archivstatus.
- Masonry: spaeter, sobald Bilder/Screenshots/PDF-Cover stabil vorhanden sind.

Empfohlene Anzeigeoptionen:

- Titel
- Beschreibung
- Notizen
- Tags
- Collections
- Domain/Adresse
- Favicon/Icon
- Favorite/Pin
- Status: active, merged duplicate, archived, broken
- Datum: hinzugefuegt, geaendert, spaeter zuletzt besucht
- Importquelle und Konfliktstatus
- Archivstatus und gespeicherte Formate, sobald Archivierung existiert

## Persistenzmodell

LinkVault sollte View-Settings spaeter nicht nur im Browser verstecken,
sondern pro Nutzer speichern. Sinnvolle erste Felder:

- `default_view`: `compact`, `detailed`, `grid`, spaeter `masonry`
- `default_sort`: `created_at`, `updated_at`, `title`, `domain`,
  `collection`, `status`
- `sort_direction`: `asc` oder `desc`
- `visible_fields`: Liste der sichtbaren Felder
- `grid_columns`: Zahl fuer Grid/Masonry
- `image_fit`: `cover` oder `contain`
- `saved_filters`: benannte Filter wie Inbox, Favorites, Duplicates,
  Unsorted, Broken, Archived

Fuer den MVP reicht eine JSON-Spalte oder einfache Settings-Tabelle. Erst wenn
mehrere Nutzer/Profile wichtig werden, braucht es ein ausgefeilteres Modell.

## Priorisierte Umsetzung

1. Bookmark-Ansichtsumschalter: Compact List, Detailed List, Grid.
2. Anzeigeoptionen fuer Titel, Beschreibung, Notizen, Tags, Collections,
   Domain, Datum, Favorite/Pin und Status.
3. Sortierung und Filter als Standard speichern, angelehnt an linkding.
4. Compact List als Default fuer Inbox und Dublettenpflege.
5. Grid/Card fuer visuelle Sichtung mit Favicon/Preview.
6. Dashboard-/Betrieb-Module nach Linkwarden-Vorbild, aber erst nach stabilen
   Bookmark-/Import-/Dedup-Workflows.
7. Masonry und Bild-Fill/Fit nach Karakeep-Vorbild, wenn Archive Worker und
   Preview-Daten stabil sind.

## Nicht Jetzt

- Masonry als Default.
- Vollwertiges Dashboard vor der stabilen Arbeitsliste.
- Pflicht-Archivierung fuer jede Installation.
- Browser-History-Spalten als Standard, weil dafuer sensiblere Daten und
  Berechtigungen noetig sind.

Die richtige Richtung ist: LinkVault wird fuer grosse Bookmark-Mengen zuerst
pflegeleicht und sicher. Danach wird es schoener und visueller.

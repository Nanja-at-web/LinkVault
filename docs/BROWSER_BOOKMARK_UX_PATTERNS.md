# Browser Bookmark UX Patterns

Datum: 2026-04-22

Diese Notiz haelt Beobachtungen aus aktuellen Browser-Oberflaechen fest:
Firefox Bibliothek/Chronik, Chrome Lesezeichenmanager, Edge Favoriten und
Import-Assistenten sowie Safari Lesezeichen/Import/Export. Die Bilder zeigen,
welche Strukturen Nutzer bereits kennen und welche Teile fuer LinkVault und
die LinkVault Companion Extension sinnvoll sind.

## Gemeinsame Browser-Muster

Browser behandeln Bookmarks meistens nicht nur als einfache Liste, sondern als
kleine Arbeitsumgebung:

- Seitenleiste mit Bereichen wie Chronik, Downloads, Schlagwoerter, alle
  Lesezeichen, Lesezeichenleiste, Lesezeichen-Menue und weitere Lesezeichen.
- Ordnerbaum fuer Favoriten/Lesezeichen mit aufklappbaren Ordnern.
- Tabellen- oder Listenansicht mit Spalten wie Name, Schlagwoerter, Adresse,
  zuletzt besucht, meistbesucht, hinzugefuegt und zuletzt veraendert.
- Sortiermenues fuer Name, Schlagwoerter, Adresse, zuletzt besucht,
  meistbesucht, hinzugefuegt und zuletzt veraendert, oft mit aufsteigend und
  absteigend.
- Detailbereich fuer ausgewaehlte Eintraege mit Name/Titel und Adresse/URL.
- Kontextmenues fuer Bearbeiten, Loeschen, Kopieren, in neuem Tab/Fenster
  oeffnen, Ordner anlegen und Import/Export.
- Import-Assistenten, die Datenquellen und Datentypen auswaehlen lassen.

Die wichtigste Ableitung: LinkVault sollte sich vertraut anfuehlen, aber nicht
versuchen, ein komplettes Browserprofil zu migrieren. Bookmarks, Ordner,
Tags/Collections, URL, Titel und Importstatus sind Kern. Passwoerter,
Autofill, Cookies und vollstaendige History bleiben ausserhalb des
Standardumfangs.

## LinkVault Web UI

Sinnvolle Uebernahmen fuer LinkVault:

- Eine klarere Bookmark-Arbeitsansicht mit Liste/Tabelle, Filtern und
  optionalen Spalten.
- Spaltenmodell fuer Titel, URL/Adresse, Domain, Tags, Collections, Status,
  hinzugefuegt und zuletzt geaendert.
- Sortierung nach Titel, Adresse/Domain, hinzugefuegt, zuletzt geaendert und
  spaeter Pflege-/Archivstatus.
- Seiten- oder Tab-Struktur mit Inbox, Bookmarks, Collections, Tags,
  Dubletten, Import, Archiv und Betrieb.
- Detail-/Editbereich fuer ausgewaehlte Bookmarks, ohne die Hauptliste zu
  verlieren.
- Kontextaktionen pro Bookmark: oeffnen, bearbeiten, favorisieren, pinnen,
  kopieren, archivieren, als Dublette markieren, loeschen.
- Import-Assistent mit Quelle, Format, Vorschau, Konflikten, Dubletten und
  finalem Import.

Nicht direkt uebernehmen:

- Browser-Verlauf als Standarddatenquelle.
- Passwort-, Autofill- oder Cookie-Import.
- Automatische Loeschaktionen ohne Vorschau, Merge-Plan oder Undo-Pfad.

## Companion Extension Filter

Die Idee, in der Companion Extension nur bestimmte Bookmarks anzuzeigen und zu
importieren, ist sehr sinnvoll. Sie reduziert Risiko bei grossen Bookmark-
Baeumen und passt zu den Browser-Vorbildern.

Gute Standardfilter ohne sensible Zusatzberechtigungen:

- Ordner/Quelle: Lesezeichenleiste, Menue, andere Lesezeichen oder ein
  einzelner Unterordner.
- Textsuche ueber Titel, URL und Ordnerpfad.
- Adresse/Domain.
- Hinzugefuegt-Datum, soweit die WebExtensions-API `dateAdded` liefert.
- Geaendert-Datum fuer Ordner, soweit `dateGroupModified` verfuegbar ist.
- Interne Duplikate im Browser-Baum.
- Bereits in LinkVault vorhandene URLs.

Tags/Schlagwoerter sind schwieriger: Firefox zeigt Schlagwoerter in der
Bibliothek, aber die WebExtensions-APIs liefern solche Daten nicht
browseruebergreifend verlaesslich. Tags sollten deshalb beim Dateiimport
genutzt werden, wenn das Quellformat sie enthaelt, aber nicht als
cross-browser Pflichtfilter der Extension gelten.

## History-Daten Nur Optional

Filter wie `zuletzt besucht` und `meistbesucht` sind produktiv, brauchen aber
Zugriff auf Browser-History. Das ist eine deutlich sensiblere Berechtigung als
`bookmarks`.

Empfehlung:

- Nicht in der Standard-Extension aktivieren.
- Spaeter als optionales Profil `History-Enrichment` anbieten.
- Nutzer muessen die `history`-Berechtigung bewusst aktivieren.
- Die Extension sollte nur aggregierte Felder an LinkVault senden:
  `last_visited_at` und `visit_count`.
- Keine vollstaendige Browser-History importieren.
- In der UI klar erklaeren, dass dies eine Datenschutz-Entscheidung ist.

## Priorisierte Umsetzung

1. Companion-Importfilter fuer Ordner, Textsuche, Adresse/Domain und
   hinzugefuegt-Datum.
2. Detailvorschau mit auswaehlbaren Links statt nur Ergebniszaehlern.
3. Web-UI-Liste mit Spaltenauswahl und Sortierung nach bekannten
   Browser-Mustern.
4. Kontextaktionen fuer Bookmarks in der Web UI.
5. Optionales History-Enrichment fuer zuletzt besucht und meistbesucht.
6. Import-Assistenten fuer weitere Formate und Tool-Profile.

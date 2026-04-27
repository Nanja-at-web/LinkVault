# Floccus-Bridge: Forschungsdokument

**Stand:** 27. April 2026
**Status:** Forschung -- keine Implementierung geplant vor Phase 4+
**Quelle:** https://github.com/floccusaddon/floccus

---

## Was ist Floccus?

Floccus ist eine Open-Source-Browser-Erweiterung fuer Firefox, Chrome und Edge,
die Browser-Lesezeichen mit einem Server-Backend synchronisiert. Unterstuetzte
Backends:

- Nextcloud Bookmarks (primaeres Backend, vollstaendig)
- WebDAV (einfacheres Format, kein Ordner-Mapping)
- LinkAce (experimentell)
- Linkwarden (experimentell)
- Google Drive / OneDrive (lokale Sync-Dateien)

Das Nextcloud-Bookmarks-Backend ist das einzige, das Floccus vollstaendig
unterstuetzt -- mit Ordnern, Tags, Zwei-Wege-Sync und Konfliktbehandlung.

---

## Wie Floccus synchronisiert

Floccus arbeitet als echter Zwei-Wege-Sync: Der Browser ist gleichwertig mit
dem Server. Jede Session:

1. Laedt den kompletten Browser-Bookmark-Baum.
2. Laedt den kompletten Server-Stand.
3. Ermittelt Differenzen (hinzugefuegt, geaendert, geloescht -- auf beiden Seiten).
4. Schreibt Aenderungen in beide Richtungen: Browser-Loeschungen loeschen auch
   auf dem Server, Server-Loeschungen loeschen auch im Browser.

Das ist ein **destruktiver Sync** -- fehlende Eintraege werden geloescht, nicht
behalten.

---

## Nextcloud-Bookmarks-API v2: Benoetiger Endpunkte

Um als Floccus-kompatibles Backend zu fungieren, muss ein Server die Nextcloud
Bookmarks API v2 (und teilweise v3) implementieren. Die Kernendpunkte:

| Methode | Pfad | Zweck |
|---|---|---|
| `GET` | `/index.php/apps/bookmarks/public/rest/v2/bookmark` | Liste mit Paginierung |
| `POST` | `/index.php/apps/bookmarks/public/rest/v2/bookmark` | Bookmark anlegen |
| `PUT` | `/index.php/apps/bookmarks/public/rest/v2/bookmark/{id}` | Bookmark aendern |
| `DELETE` | `/index.php/apps/bookmarks/public/rest/v2/bookmark/{id}` | Bookmark loeschen |
| `GET` | `/index.php/apps/bookmarks/public/rest/v2/folder` | Ordner-Baum |
| `POST` | `/index.php/apps/bookmarks/public/rest/v2/folder` | Ordner anlegen |
| `PUT` | `/index.php/apps/bookmarks/public/rest/v2/folder/{id}` | Ordner umbenennen |
| `DELETE` | `/index.php/apps/bookmarks/public/rest/v2/folder/{id}` | Ordner loeschen |
| `GET` | `/index.php/apps/bookmarks/public/rest/v2/folder/{id}/children` | Kinder eines Ordners |
| `POST` | `/index.php/apps/bookmarks/public/rest/v2/folder/{id}/bookmark/{bid}` | Bookmark in Ordner haengen |
| `DELETE` | `/index.php/apps/bookmarks/public/rest/v2/folder/{id}/bookmark/{bid}` | Bookmark aus Ordner entfernen |
| `GET` | `/index.php/apps/bookmarks/public/rest/v2/bookmark/{id}/tags` | Tags eines Bookmarks |
| `POST` | `/index.php/apps/bookmarks/public/rest/v2/bookmark/{id}/tags` | Tags setzen |
| `GET` | `/ocs/v1.php/cloud/user` | Benutzerinfo (Nextcloud OCS) |
| `GET` | `/status.php` | Nextcloud-Statusdatei fuer Discovery |

Das ergibt **mindestens 15 Endpunkte** -- plus Paginierungslogik, OCS-Antwort-
Format (XML oder JSON je nach Header), Nextcloud-Authentifizierung via
Basic Auth oder App-Passwort.

---

## Technische Konflikte mit LinkVault

### 1. Destruktiver Sync vs. No-Hard-Delete

LinkVaults Kernprinzip: kein Merge loescht Daten, Undo bleibt immer moeglich.
Floccus-Sync loescht Bookmarks hart, wenn sie im Browser fehlen. Diese
Philosophien sind unvereinbar ohne eine explizite Schutzschicht.

Loesungsansaetze, die alle Kompromisse erfordern:

- **Soft-Delete-Bridge:** Floccus-DELETE markiert als `floccus_deleted` statt
  echter Loeschung -- Floccus bemerkt das nicht, fuehrt aber beim naechsten
  Sync wieder eine Loeschung durch, weil der Eintrag serverseitig noch
  vorhanden ist.
- **Schreibschutz-Modus:** Server akzeptiert nur GET, keine DELETE -- Floccus
  bricht den Sync ab, weil Writes fehlschlagen.
- **Einbahnstrassen-Sync:** Nur Browser → Server (kein Server → Browser) --
  nicht das, was Floccus erwartet, und nicht konfigurierbar in Floccus ohne
  eigene Extension-Fork.

### 2. Datenmodell-Mismatch: Ordner vs. Tags/Collections

Floccus kennt nur **Ordner** (hierarchische Baumstruktur). LinkVault verwendet:

- **Tags** -- flache Labels, viele pro Bookmark
- **Collections** -- Ordnerpfad-Notation (`Homelab/Proxmox`), aber kein echter
  Baum in der Datenbank

Mapping-Optionen:

| Floccus-Ordner | LinkVault | Problem |
|---|---|---|
| Ordnerpfad → Collection | Naheliegend | Tiefe Baeume werden zu langen Pfadstrings |
| Oberster Ordner → Tag | Zu verlustreich | Unterordner fallen weg |
| Ordner → Tag + Pfad | Hybrid | Komplex, schlecht umkehrbar |

Ein sauberes Mapping ohne Datenverlust ist nicht moeglich, weil Floccus einen
echten Baum erwartet und LinkVault intern keine Baum-Tabelle hat.

### 3. Auth-Modell

Nextcloud-Auth verwendet Basic Auth mit App-Passwort-Format oder Nextcloud
Session. LinkVaults Auth ist session-basiert mit eigenem API-Token-Format.
Fuer Floccus muesste LinkVault Basic Auth akzeptieren und das Nextcloud
OCS-Benutzerformat (`/ocs/v1.php/cloud/user`) zurueckgeben.

### 4. Nextcloud-Discovery

Floccus erkennt Nextcloud-Instanzen anhand von `/status.php` mit einem
spezifischen JSON-Format (`{"installed":true,"version":"...","productname":...}`).
LinkVault muesste dieses Format nachahmen, was eine Versionsnummer erfordert,
die kompatibel mit der erwarteten Nextcloud-Mindestversion ist.

---

## Beziehung zur bestehenden Infrastruktur

LinkVault hat bereits:

- `sync_snapshots`-Tabelle -- speichert Browser-Stand als Zeitpunkt-Baseline
- `record_sync_snapshot()` -- nimmt Browser-Items entgegen, speichert als JSON
- `compute_sync_drift()` -- vergleicht aktuellen Browser-Stand mit Snapshot,
  vier Kategorien: `deleted_from_browser`, `added_to_browser`, `diverged`,
  `linkvault_only`
- Companion Extension mit Discovery, Export und sicherem Restore

Diese Infrastruktur deckt den **sicheren einseitigen Restore-Fall** ab:
Browser → LinkVault mit Konfliktentscheidung, kein Datenverlust.

Floccus erwartet den **echten Zwei-Wege-Fall**: beide Seiten aendern, beide
Seiten loeschen, Server ist der Wahrheitsgeber.

Die Drift-Erkennung koennte als Grundlage fuer eine spaetere Floccus-Bridge
dienen -- aber nur, wenn das Loeschproblem geloest ist.

---

## Designentscheidungen vor einer Implementierung

Bevor eine Floccus-Bridge implementiert werden kann, muessen diese Fragen
beantwortet werden:

1. **Loeschphilosophie:** Gibt es eine Kategorie von Bookmarks, die hartes
   Loeschen erlaubt? (z.B. Inbox-Bookmarks, die noch nicht kategorisiert sind)
   Oder bleibt No-Hard-Delete absolut?

2. **Ordner-Mapping:** Welches Mapping ist kanonikisch fuer den Hin- und
   Rueckweg? Ordnerpfad → Collection-Pfad ist das Naheliegendste, aber
   Round-Trip-Sicherheit muss geprueft werden.

3. **Sync-Scope:** Soll Floccus-Sync einen eigenen Namespace bekommen
   (z.B. alle Bookmarks mit `sync_source='floccus'`) oder den vollen
   LinkVault-Bestand sehen?

4. **Konfliktmodell:** Wie werden echte Zwei-Wege-Konflikte angezeigt --
   im Conflict Center, in der Extension, oder in einer eigenen Sync-UI?

5. **Auth:** Separates App-Passwort fuer Floccus, oder dasselbe API-Token-
   System? Basic-Auth-Adapter notwendig?

---

## Abgrenzung zur Companion Extension

Die Companion Extension ist der **primaere Browser-Sync-Pfad** fuer LinkVault:

- Firefox/Chromium-native, kein Drittanbieter
- Sicherer Restore (keine Loeschungen ohne explizite Entscheidung)
- Conflict Center fuer Einzelfallentscheidungen
- Vollstaendige Kontrolle ueber Protokoll und Datenschema

Floccus waere ein **kompatibler Alternativpfad** fuer Nutzer, die bereits
Floccus verwenden und LinkVault als weiteres Backend einbinden wollen --
kein Ersatz fuer die Companion Extension.

---

## Empfehlung und Timing

**Nicht vor Phase 4** (nach Companion-Extension-Packaging).

Voraussetzungen fuer eine Floccus-Bridge:

1. Companion Extension ist stabil und gepackt.
2. Conflict Center deckt Zwei-Wege-Konflikte vollstaendig ab.
3. Loeschphilosophie ist explizit fuer Sync-Kontext entschieden.
4. Nextcloud-Bookmarks-API v2 ist vollstaendig dokumentiert und getestet.

Alternativ: Kontakt zu Floccus-Maintainern aufnehmen, um ein leichtgewichtigeres
"LinkVault Native"-Backend-Protokoll zu erkunden (aehnlich wie LinkAce-Support
in Floccus), das kein vollstaendiges Nextcloud-Emulat erfordert.

---

## Quellen

- Floccus GitHub: https://github.com/floccusaddon/floccus
- Nextcloud Bookmarks API: https://github.com/nickvdyck/nextcloud-bookmarks
- Floccus Backend-Interface: https://github.com/floccusaddon/floccus/tree/develop/src/lib/adapters
- LinkAce-Adapter als Referenz: https://github.com/floccusaddon/floccus/blob/develop/src/lib/adapters/LinkAce.ts

# Research Impact

## Quelle

Diese Auswertung basiert auf der lokalen Deep-Research-Sammlung
`Deep-Research-Sammlung zu Selfhosted Bookmark- und Archivierungs-Tools`
vom 19.04.2026. Die Sammlung vergleicht Karakeep, linkding, Linkwarden,
LinkAce, Readeck, Shiori und community-scripts.org.

Am 20.04.2026 wurden zusaetzlich das `LinkVault Forschungs-Paket fuer
Selfhosted Bookmark- und Archiv-Apps` und das `LinkVault Browser API Research
Bundle` ausgewertet. Diese erweitern den Tool-Vergleich um Omnivore, Betula,
Grimoire, Shaarli und Wallabag und schaerfen besonders Import, Browser-APIs,
Sync, Vendor-Metadaten und kanonisches Import-Schema.

Die wichtigste Wirkung auf LinkVault: Das Projekt sollte keine reine Kopie
eines bestehenden Tools werden, sondern eine klare Synthese aus spezialisierten
Staerken.

## Produktformel

LinkVault sollte diese Produktlinie verfolgen:

```text
linkding-artige URL-Deduplizierung
+ Karakeep-artige Favoriten, Listen, Regeln und AI-Optionen
+ Linkwarden-artige Archivformate und Collections
+ Readeck-artige Reader-/Highlight- und leichte Speicherlogik
+ LinkAce-artige Multiuser-, SSO-, API- und Monitoring-Reife
+ Shiori-artige Einfachheit im Betrieb
+ community-scripts-artige Proxmox-LXC-Installation
```

## Einfluss Auf Das Produkt

### 1. Dedup ist das zentrale Differenzierungsmerkmal

Die Recherche zeigt: Viele Tools haben URL-Pruefungen oder Import-Schutz, aber
kaum eines bietet einen wirklich sicheren, sichtbaren Merge-Workflow.

Konsequenz fuer LinkVault:

- Dedup bleibt ein Kernmodul, nicht nur ein Import-Detail.
- Jeder Merge braucht Dry-Run, Gewinner-Vorschlag und spaeter Undo.
- Merge darf Archive, Highlights, Notizen, Tags, Collections, Favoriten und
  Pins nicht verlieren.
- LinkVault sollte Dubletten auch als Pflegeaufgabe fuer Favoriten behandeln.

### 2. Archivierung darf nicht nur "Datei speichern" sein

Linkwarden und Readeck zeigen zwei wichtige Richtungen:

- Linkwarden: Screenshot, PDF, Single-HTML, Reader View, Annotationen.
- Readeck: leichte lokale Inhaltskopie, Highlights, EPUB/OPDS, SQLite/Go-Nahe.

Konsequenz fuer LinkVault:

- Zuerst Reader-Extrakt und persistente Archive planen.
- Danach Screenshot/PDF/Single-HTML als optionale Worker-Funktionen.
- Archivassets muessen beim Dedup/Merge eine eigene Rolle bekommen.
- Backup/Restore muss spaeter neben SQLite auch Archivdateien abdecken.

### 3. Organisation muss zwei Ebenen haben

Die Referenztools trennen oft Tags, Listen, Collections, Bundles oder Labels.
Die Recherche bestaetigt: LinkVault braucht flexible Tags und strukturierte
Collections.

Konsequenz fuer LinkVault:

- Tags bleiben frei und mehrfach.
- Collections sollen hierarchisch sein.
- Smart Collections sollen gespeicherte Filter sein.
- Bundles/kuratierte Link-Sets koennen spaeter als Teilen-/Export-Funktion
  kommen.

### 4. Auth und API sind frueher wichtig als gedacht

linkding, LinkAce, Linkwarden und Karakeep zeigen, dass API, OIDC/Auth-Proxy
und Multiuser/Teams schnell relevant werden.

Konsequenz fuer LinkVault:

- Single-User-Setup und Login muessen vor einer breiteren Proxmox-Empfehlung
  kommen.
- API-Token sollten frueh geplant werden, weil Import, Browser-Extension,
  Sync und Automatisierung darauf aufbauen.
- OIDC/Reverse-Proxy-Auth bleibt ein klares Selfhost-Ziel.

### 5. Proxmox ist nicht nur Packaging, sondern Produktqualitaet

community-scripts.org ist kein Bookmark-Tool, aber ein harter Praxisfilter:
Installation, Updates, Logs, Healthcheck, Backup und Ressourcen muessen
reproduzierbar sein.

Konsequenz fuer LinkVault:

- Der vorhandene Proxmox-Einzeiler ist ein wichtiger MVP-Meilenstein.
- Vor einer offiziellen Einreichung fehlen Update-Funktion,
  Backup/Restore-Test im LXC und community-scripts-Konventionen.
- LinkVault sollte leichtgewichtig bleiben, solange Archiv-Worker optional
  sind.

## Einfluss Auf Die Roadmap

Die naechsten Schritte verschieben sich dadurch etwas:

1. **Single-User-Auth und Setup-Token** vor weiterer Verbreitung.
2. **Dedup-Dashboard mit Merge-Dry-Run in der UI** als Kernnutzen.
3. **Backup/Restore im echten LXC testen**, weil Proxmox bereits laeuft.
4. **Bookmark-Bearbeitung und Bulk-Aktionen** fuer echte Datenpflege.
5. **Reader-Extrakt + Archivstatus** vor Screenshot/PDF.
6. **API-Token** vor Browser-Extension und Importprofilen.
7. **community-scripts-Konformitaet** erst nach Update-/Backup-Pfad.

## Bewusste Nicht-Ziele Im MVP

- Kein sofortiger Karakeep-/Linkwarden-Funktionsumfang mit voller AI,
  Mobile-App und Mehrformatarchivierung.
- Kein automatisches Loeschen von Dubletten ohne Undo.
- Keine Pflicht zu PostgreSQL, Redis oder Browserless im leichten MVP.
- Keine community-scripts.org-Einreichung, bevor Update und Restore in LXC
  getestet sind.

## Aktualisierte Prioritaet Der Vorbilder

| Bereich | Staerkste Vorlage | LinkVault-Folge |
|---|---|---|
| URL-Dedup/API | linkding | robuste Normalisierung, Check-Endpunkte, API-Token |
| Favoriten/Regeln/AI | Karakeep | Favoritenpflege, Smart Lists, Regeln, optionale AI |
| Archivformate | Linkwarden | Single-HTML/PDF/Screenshot spaeter als Worker |
| Reader/Highlights | Readeck | leichter Reader-Extrakt und Highlights frueh planen |
| SSO/Multiuser/Monitoring | LinkAce | Auth, Health Checks, API und Admin-Reife |
| Einfacher Betrieb | Shiori/Readeck | kleine Defaults, wenig Pflichtdienste |
| Proxmox-UX | community-scripts.org | Einzeiler, Logs, Update, Backup, Restore |

## Neue Ableitungen Vom 20.04.2026

### Browser-Import Ist Ein Eigenes Produktmodul

Das Browser-Research zeigt: Netscape-HTML ist der breite Austauschstandard,
aber kein vollstaendiges Datenmodell. Chrome/Chromium, Firefox und Safari
haben jeweils eigene Zusatzformate und Sync-Eigenheiten.

Konsequenz fuer LinkVault:

- Browser-HTML bleibt der MVP-Baseline-Import.
- Import-Sessions sollen Quelle, Datei, Checksumme, Profil, Format und
  Ergebniszahlen speichern.
- Chromium-JSON, Firefox-JSON/JSONLZ4 und Safari-ZIP werden als spaetere
  Enrichment-Importer geplant.
- Vendor-Rohdaten duerfen nicht verloren gehen, sondern sollen optional als
  `raw_vendor_payload` erhalten bleiben.

### Sync Ist Nicht Gleich Backup

Mehrere Browser behandeln Sync als Zusammenfuehrung zwischen Geraeten, nicht
als verlaesslichen Backup-Stand. Das passt zu LinkVaults nicht-destruktivem
Merge-Ansatz.

Konsequenz fuer LinkVault:

- Sync-Importe bekommen eine eigene Herkunft (`sync_origin`).
- Import, Sync und Merge muessen in einem Conflict Center sichtbar werden.
- Vor jedem grossen Import braucht es Dry-Run, Snapshot und Duplikatbericht.

### Vergleichsrahmen Wird Breiter

Die neuen Tool-Daten zeigen weitere Vorbilder:

- Wallabag: Reader-UX, Annotationen, Importvielfalt und API-Reife.
- Shaarli: extrem niedriger Betriebsaufwand, Sticky/Pinning, API und
  HTML-Import/Export.
- Omnivore: Lesefluss, Highlights, Suchsyntax und Cross-Device-Ideen, aber
  vorsichtig wegen Produktgeschichte.
- Grimoire: moderne UI und API, aber Import/Export teils noch Roadmap.
- Betula: Ein-Binary/SQLite und privacy-first/federierte Nische.

Konsequenz fuer LinkVault:

- LinkVaults Chance bleibt die Luecke zwischen leichtem Selfhosting und
  starker Datenpflege.
- Der naechste Import-Ausbau sollte zuerst sicher und transparent sein, nicht
  sofort vollautomatisch.

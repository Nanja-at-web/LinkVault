# Dubletten, Sortierung und Kategorisierung

## Dubletten-Workflow

1. Import oder neuer Link kommt herein.
2. URL wird normalisiert.
3. Redirects und Canonical-Metadaten werden ermittelt.
4. Fingerprints werden gespeichert:
   - normalized URL
   - redirect target
   - canonical URL
   - domain
   - slug
   - title fingerprint
   - content hash
5. Kandidatengruppen werden gebildet.
6. Ein Merge-Plan wird vorgeschlagen.
7. Nutzer prueft Dry-Run.
8. Merge uebernimmt alle nutzbaren Daten.
9. Undo-Information wird gespeichert.

## Siegerauswahl

Wenn mehrere Favoriten dieselbe Seite meinen, gewinnt der Eintrag mit der
hoechsten Datenqualitaet:

1. gepinnt
2. favorisiert
3. besitzt Highlights
4. besitzt manuelle Notizen
5. besitzt vollstaendige Archive
6. besitzt mehr Tags/Collections
7. wurde haeufiger geoeffnet
8. ist aelter und damit wahrscheinlicher der Ursprungseintrag

## Was beim Merge erhalten bleibt

- alle Tags
- alle Collections inklusive Positionen
- Favoriten- und Pin-Status
- Highlights und Notizen
- Archivdateien
- Importquelle
- Redirect-Historie
- Health-Check-Historie
- manuelle Titel/Beschreibungen, falls sie besser sind

## Bulk-Bereinigung

Die Admin-Ansicht braucht drei Modi:

- `Sicher`: nur Score >= 95, keine widerspruechlichen Metadaten.
- `Review`: Score 80-94, Nutzer entscheidet.
- `Aehnlich`: Score 60-79, eher zum Gruppieren oder Taggen.

Jede Massenaktion muss zeigen:

- Anzahl betroffener Items
- Gewinner je Gruppe
- welche Tags/Collections verschoben werden
- ob Archive erhalten bleiben
- ob Verlierer nur versteckt oder geloescht werden

## Automatisches Sortieren

LinkVault sortiert nicht nur alphabetisch. Es sollte mehrere Perspektiven
geben:

- `Heute wichtig`: Favoriten, neue Links, kaputte Links, ungelesene Pins.
- `Aufraeumen`: Dubletten, fehlende Titel, fehlende Tags, tote Links.
- `Lesen`: ungelesen, kurze Lesedauer zuerst, spaeter lesen.
- `Wissen`: haeufig verwendete Domains, Themencluster, Autoren.
- `Archiv`: Webseiten mit fehlendem Screenshot/PDF/Single-HTML.

## Kategorisierung

Kategorisierung kombiniert Regeln, Heuristiken und AI-Vorschlaege:

- Domain-Regeln: `github.com` -> Development.
- Pfad-Regeln: `/docs/` -> Documentation.
- Inhaltstyp: PDF -> Papers oder Documents.
- Sprache: deutsche Links in deutsche Collections.
- Titel/Text: Begriffe wie `Proxmox`, `LXC`, `Docker` -> Homelab.
- Nutzerverhalten: haeufig favorisierte Domains bekommen Vorschlaege.
- AI: erzeugt Tags und Collection-Vorschlag mit kurzer Begruendung.

## Regelbeispiele

```yaml
- name: Proxmox Homelab
  when:
    any:
      - domain_contains: proxmox
      - text_contains: ["LXC", "Proxmox VE", "community-scripts"]
  then:
    add_tags: ["proxmox", "homelab"]
    add_collection: "Homelab/Proxmox"
    priority: high

- name: Rezeptseiten
  when:
    any:
      - schema_type: Recipe
      - text_contains: ["Zutaten", "Zubereitung"]
  then:
    add_tags: ["recipe", "cooking"]
    add_collection: "Privat/Rezepte"
```

## UI-Anforderungen fuer Favoritenpflege

- Favoriten-Dashboard mit Drag-and-drop-Reihenfolge.
- Doppelte Favoriten prominent anzeigen.
- "Favorit behalten, Dublette mergen" als eigene Aktion.
- Filter: Favoriten ohne Kategorie, Favoriten ohne Archiv, tote Favoriten.
- Bulk-Aktion: Favoriten in Collection verschieben, Tags setzen, Pins setzen.

## Qualitaetsmetriken

LinkVault sollte pro Sammlung einen Pflege-Score anzeigen:

- Prozent der Links mit Titel/Beschreibung.
- Prozent archivierter Links.
- Anzahl Dublettengruppen.
- Anzahl toter Links.
- Anteil kategorisierter Favoriten.
- Anzahl Links ohne Tags.

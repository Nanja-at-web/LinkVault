# LinkVault Companion Extension Updates

## Kurzfassung

Waehrend der Entwicklung muss die temporaere Extension nicht jedes Mal
entfernt und neu installiert werden. In Firefox reicht normalerweise
`about:debugging` -> `LinkVault Companion` -> `Reload`. In Chromium-basierten
Browsern reicht die Reload-Schaltflaeche fuer die entpackte Extension.

Wichtig ist: dieselbe lokale Extension aus demselben Ordner laden.

## Token und URL behalten

Die Companion Extension speichert LinkVault-URL und API-Token in
`storage.local` des Browsers. Die Firefox-Extension hat dafuer eine stabile
ID im Manifest:

```json
"browser_specific_settings": {
  "gecko": {
    "id": "linkvault-companion@nanja-at-web.local"
  }
}
```

Dadurch bleibt die Extension-Identitaet beim Reload stabiler. Wenn die
Extension nur neu geladen wird, bleiben URL und Token normalerweise erhalten.

Wenn die Extension komplett entfernt oder aus einem anderen Ordner neu geladen
wird, kann der Browser sie als neue Installation behandeln. Dann muessen URL
und Token erneut eingetragen werden.

## Warum kein Ajax-Selbstupdate?

Ajax oder eine andere Programmiersprache kann Extension-Code nicht einfach
selbst ersetzen. Browser blockieren das absichtlich: Erweiterungen duerfen
ihren eigenen Code nicht beliebig aus dem Netzwerk nachladen und ausfuehren,
weil das ein Sicherheitsrisiko waere.

Die sinnvollen Update-Wege sind:

- Entwicklung: lokale Dateien aktualisieren und Extension im Browser neu
  laden.
- Spaeter: signiertes Firefox-Addon oder gepackte Chromium-Extension mit
  offiziellem Updatekanal.
- Optional spaeter fuer Homelab/Enterprise: eigenes Update-Manifest mit
  signiertem Paket, wenn der jeweilige Browser das fuer diesen Installationsweg
  erlaubt.

## Praktische Befehle

LinkVault im Proxmox-LXC aktualisieren:

```bash
pct exec 112 -- linkvault-helper update
```

Danach im Browser nur die Extension neu laden:

- Firefox: `about:debugging#/runtime/this-firefox` -> `Reload`
- Chrome/Edge/Brave/Vivaldi/Opera: `Extensions` -> Developer mode -> Reload
  beim entpackten `LinkVault Companion`

## Spaeterer Ausbau

Fuer eine bequemere Nutzerverteilung braucht LinkVault spaeter:

- Extension-Paketierung als ZIP/CRX/XPI-Vorstufe.
- Signatur/Store-Verteilung fuer Firefox und Chromium.
- Versionsanzeige in LinkVault und in der Companion Extension.
- Update-Hinweis in LinkVault, wenn Extension und Server nicht zusammenpassen.


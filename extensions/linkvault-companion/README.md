# LinkVault Companion Extension

Developer preview for importing browser bookmarks directly into LinkVault.

## Current Features

- Store LinkVault URL and API token.
- Test LinkVault health and token access.
- Save the current tab as a bookmark.
- Read browser bookmarks with the WebExtensions `bookmarks` API.
- Select all browser bookmarks or one browser folder before preview/import.
- Send a browser-bookmark import preview to LinkVault.
- Import browser bookmarks into LinkVault.

## Load In Firefox

1. Open `about:debugging#/runtime/this-firefox`.
2. Click `Load Temporary Add-on`.
3. Select `extensions/linkvault-companion/manifest.json`.
4. Open the extension options.
5. Enter the LinkVault URL, for example `http://192.168.1.190:3080`.
6. Enter an API token created in LinkVault under `Betrieb`.
7. Run `Test connection`.

## Load In Chrome, Edge, Brave, Vivaldi Or Opera

1. Open the browser's extensions page.
2. Enable developer mode.
3. Choose `Load unpacked`.
4. Select the `extensions/linkvault-companion` folder.
5. Open options and add LinkVault URL plus API token.

## Notes

This first version is intentionally one-way:

- Browser to LinkVault only.
- No browser bookmark deletion.
- No two-way sync.
- No history, password, form-fill or profile import.
- Internal browser URLs such as `about:`, `place:` or `moz-extension:` are
  skipped because LinkVault only stores regular HTTP/HTTPS bookmarks.
- Folder selection imports the selected folder and its subfolders. Individual
  per-link selection is planned after the folder-based flow is stable.

## Troubleshooting

If `Test connection` fails:

1. Open `http://YOUR-LINKVAULT-IP:3080/healthz` in a normal browser tab.
   It should return JSON with `"ok": true`.
2. Update LinkVault in the LXC so the CORS/OPTIONS support is present.
3. Remove and reload the temporary extension after each extension code update.
4. When Firefox asks for host/network permission, allow access to the
   LinkVault host.
5. Check that the API token was copied completely and still exists under
   LinkVault `Betrieb`.
6. If the normal tab cannot open `/healthz`, the problem is network, IP,
   container status or firewall, not the extension.

LinkVault commonly runs as plain HTTP inside a trusted homelab/LXC network.
The extension manifest therefore explicitly allows HTTP API connections to
self-hosted LinkVault instances. If Firefox shows a warning about upgrading
`http://.../healthz` to `https://.../healthz`, reload the latest extension from
`manifest.json`; older temporary loads may still use the previous manifest.

Firefox requires the permission prompt to happen directly from the button
click. If permission errors persist after updating the extension, remove the
temporary add-on and load it again from `manifest.json`.

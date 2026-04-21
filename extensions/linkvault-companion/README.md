# LinkVault Companion Extension

Developer preview for importing browser bookmarks directly into LinkVault.

## Current Features

- Store LinkVault URL and API token.
- Test LinkVault health and token access.
- Save the current tab as a bookmark.
- Read browser bookmarks with the WebExtensions `bookmarks` API.
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

const resultEl = document.querySelector("#result");
const connectionState = document.querySelector("#connection-state");
const bookmarkSourceEl = document.querySelector("#bookmark-source");

function showResult(message, kind = "info") {
  resultEl.textContent = message;
  resultEl.className = `status ${kind}`;
}

function summarizePreview(payload) {
  const invalid = payload.invalid_skipped ? `, ${payload.invalid_skipped} internal/invalid skipped` : "";
  return `${payload.total} found, ${payload.create} new, ${payload.duplicate_existing} already in LinkVault, ${payload.duplicate_in_import} duplicates inside browser bookmarks${invalid}.`;
}

async function refreshConnectionState() {
  const settings = await getSettings();
  if (!settings.linkvaultUrl || !settings.apiToken) {
    connectionState.textContent = "Open Options and add LinkVault URL plus API token.";
    return;
  }
  connectionState.textContent = `Connected to ${settings.linkvaultUrl}`;
}

async function refreshBookmarkSources() {
  const currentValue = bookmarkSourceEl.value;
  const folders = await browserBookmarkFolders();
  bookmarkSourceEl.innerHTML = '<option value="">All browser bookmarks</option>';
  for (const folder of folders) {
    const option = document.createElement("option");
    option.value = folder.id;
    option.textContent = `${folder.path} (${folder.count})`;
    bookmarkSourceEl.append(option);
  }
  if ([...bookmarkSourceEl.options].some((option) => option.value === currentValue)) {
    bookmarkSourceEl.value = currentValue;
  }
}

function selectedBookmarkSource() {
  return {rootId: bookmarkSourceEl.value};
}

document.querySelector("#open-options").addEventListener("click", () => {
  linkvaultRuntime.runtime.openOptionsPage();
});

document.querySelector("#refresh-bookmark-sources").addEventListener("click", async () => {
  try {
    showResult("Reading bookmark folders...");
    await refreshBookmarkSources();
    showResult("Bookmark folders refreshed.", "ok");
  } catch (error) {
    showResult(error.message, "error");
  }
});

document.querySelector("#save-current-tab").addEventListener("click", async () => {
  try {
    const bookmark = await saveCurrentTab({
      tags: document.querySelector("#save-tags").value,
      collections: document.querySelector("#save-collections").value,
      notes: document.querySelector("#save-notes").value,
      favorite: document.querySelector("#save-favorite").checked,
      pinned: document.querySelector("#save-pinned").checked
    });
    showResult(`Saved: ${bookmark.title || bookmark.url}`, "ok");
  } catch (error) {
    if (error.status === 409 && error.payload?.preflight?.matches?.length) {
      showResult("Possible duplicate found in LinkVault. Open LinkVault to decide whether to update or save separately.", "error");
      return;
    }
    showResult(error.message, "error");
  }
});

document.querySelector("#preview-bookmarks").addEventListener("click", async () => {
  try {
    showResult("Reading browser bookmarks...");
    const preview = await previewBrowserBookmarks(selectedBookmarkSource());
    showResult(summarizePreview(preview), "ok");
  } catch (error) {
    showResult(error.message, "error");
  }
});

document.querySelector("#import-bookmarks").addEventListener("click", async () => {
  try {
    showResult("Importing browser bookmarks...");
    const result = await importBrowserBookmarks(selectedBookmarkSource());
    const invalid = result.invalid_skipped ? `, ${result.invalid_skipped} internal/invalid skipped` : "";
    showResult(`${result.created} imported, ${result.duplicates_skipped} duplicates skipped${invalid}.`, "ok");
  } catch (error) {
    showResult(error.message, "error");
  }
});

refreshConnectionState();
refreshBookmarkSources().catch((error) => showResult(error.message, "error"));

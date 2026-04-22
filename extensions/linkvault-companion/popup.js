const resultEl = document.querySelector("#result");
const connectionState = document.querySelector("#connection-state");
const bookmarkSourceEl = document.querySelector("#bookmark-source");
const previewDetailsEl = document.querySelector("#preview-details");
const bookmarkFilterQueryEl = document.querySelector("#bookmark-filter-query");
const bookmarkFilterDomainEl = document.querySelector("#bookmark-filter-domain");
const bookmarkFilterAddedFromEl = document.querySelector("#bookmark-filter-added-from");
const bookmarkFilterAddedToEl = document.querySelector("#bookmark-filter-added-to");
const PREVIEW_DETAIL_LIMIT = 30;

function showResult(message, kind = "info") {
  resultEl.textContent = message;
  resultEl.className = `status ${kind}`;
}

function summarizePreview(payload) {
  const invalid = payload.invalid_skipped ? `, ${payload.invalid_skipped} internal/invalid skipped` : "";
  return `${payload.total} found, ${payload.create} new, ${payload.duplicate_existing} already in LinkVault, ${payload.duplicate_in_import} duplicates inside browser bookmarks${invalid}.`;
}

function clearPreviewDetails() {
  previewDetailsEl.replaceChildren();
  previewDetailsEl.hidden = true;
}

function renderPreviewDetails(payload) {
  previewDetailsEl.replaceChildren();
  previewDetailsEl.hidden = false;

  const heading = document.createElement("h2");
  heading.textContent = "Preview details";
  previewDetailsEl.append(heading);

  const records = (payload.records || []).slice(0, PREVIEW_DETAIL_LIMIT);
  if (!records.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No bookmark rows to show.";
    previewDetailsEl.append(empty);
    return;
  }

  const note = document.createElement("p");
  note.className = "muted";
  note.textContent = `Showing ${records.length} of ${payload.total} rows. Choose a smaller folder for a tighter review.`;
  previewDetailsEl.append(note);

  const list = document.createElement("div");
  list.className = "preview-list";
  for (const record of records) {
    list.append(previewRow(record));
  }
  previewDetailsEl.append(list);
}

function previewRow(record) {
  const row = document.createElement("article");
  row.className = `preview-row ${record.action || ""}`;

  const title = document.createElement("strong");
  title.textContent = record.title || record.url || "Untitled bookmark";

  const action = document.createElement("span");
  action.className = "pill";
  action.textContent = previewActionLabel(record.action);

  const header = document.createElement("div");
  header.className = "preview-row-header";
  header.append(title, action);

  const url = document.createElement("p");
  url.className = "preview-url";
  url.textContent = record.url || "-";

  const meta = document.createElement("p");
  meta.className = "muted";
  meta.textContent = [
    record.domain || "-",
    `collections: ${(record.collections || []).join(", ") || "-"}`,
    `tags: ${(record.tags || []).join(", ") || "-"}`
  ].join(" - ");

  row.append(header, url, meta);

  if (record.duplicate_bookmark) {
    const duplicate = document.createElement("p");
    duplicate.className = "muted";
    duplicate.textContent = `Already in LinkVault: ${record.duplicate_bookmark.title || record.duplicate_bookmark.url}`;
    row.append(duplicate);
  } else if (record.duplicate_of_index) {
    const duplicate = document.createElement("p");
    duplicate.className = "muted";
    duplicate.textContent = `Duplicate of import row ${record.duplicate_of_index}`;
    row.append(duplicate);
  } else if (record.error) {
    const error = document.createElement("p");
    error.className = "muted";
    error.textContent = record.error;
    row.append(error);
  }

  return row;
}

function previewActionLabel(action) {
  return {
    create: "New",
    duplicate_existing: "Exists",
    duplicate_in_import: "Duplicate",
    invalid_skipped: "Skipped"
  }[action] || action || "Unknown";
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
  return {
    rootId: bookmarkSourceEl.value,
    filters: {
      query: bookmarkFilterQueryEl.value,
      domain: bookmarkFilterDomainEl.value,
      addedFrom: bookmarkFilterAddedFromEl.value,
      addedTo: bookmarkFilterAddedToEl.value
    }
  };
}

document.querySelector("#open-options").addEventListener("click", () => {
  linkvaultRuntime.runtime.openOptionsPage();
});

document.querySelector("#refresh-bookmark-sources").addEventListener("click", async () => {
  try {
    clearPreviewDetails();
    showResult("Reading bookmark folders...");
    await refreshBookmarkSources();
    showResult("Bookmark folders refreshed.", "ok");
  } catch (error) {
    showResult(error.message, "error");
  }
});

document.querySelector("#clear-bookmark-filters").addEventListener("click", () => {
  bookmarkFilterQueryEl.value = "";
  bookmarkFilterDomainEl.value = "";
  bookmarkFilterAddedFromEl.value = "";
  bookmarkFilterAddedToEl.value = "";
  clearPreviewDetails();
  showResult("Bookmark filters cleared.");
});

document.querySelector("#save-current-tab").addEventListener("click", async () => {
  try {
    clearPreviewDetails();
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
    renderPreviewDetails(preview);
  } catch (error) {
    clearPreviewDetails();
    showResult(error.message, "error");
  }
});

document.querySelector("#import-bookmarks").addEventListener("click", async () => {
  try {
    clearPreviewDetails();
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

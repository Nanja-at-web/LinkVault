const resultEl = document.querySelector("#result");
const connectionState = document.querySelector("#connection-state");
const bookmarkSourceEl = document.querySelector("#bookmark-source");
const previewDetailsEl = document.querySelector("#preview-details");
const bookmarkFilterQueryEl = document.querySelector("#bookmark-filter-query");
const bookmarkFilterDomainEl = document.querySelector("#bookmark-filter-domain");
const bookmarkFilterAddedFromEl = document.querySelector("#bookmark-filter-added-from");
const bookmarkFilterAddedToEl = document.querySelector("#bookmark-filter-added-to");
const browserRestoreTargetFolderEl = document.querySelector("#browser-restore-target-folder");
const browserRestoreTargetModeEl = document.querySelector("#browser-restore-target-mode");
const browserRestoreFolderNameEl = document.querySelector("#browser-restore-folder-name");
const browserRestoreDuplicatesEl = document.querySelector("#browser-restore-duplicates");
const linkvaultExportQueryEl = document.querySelector("#linkvault-export-query");
const linkvaultExportCollectionEl = document.querySelector("#linkvault-export-collection");
const linkvaultExportFavoriteEl = document.querySelector("#linkvault-export-favorite");
const linkvaultExportPinnedEl = document.querySelector("#linkvault-export-pinned");
const PREVIEW_DETAIL_LIMIT = 30;
let lastBrowserRestorePreview = null;
let lastBrowserRestorePreviewKey = "";
let lastBrowserRestoreDecisions = {};

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
    `tags: ${(record.tags || []).join(", ") || "-"}`,
    `source: ${record.source_folder_path || record.source_root || "-"}`
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
    invalid_skipped: "Skipped",
    skip_existing: "Skip existing",
    update_existing: "Update existing",
    merge_existing: "Merge metadata"
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
  const targetValue = browserRestoreTargetFolderEl.value;
  const sourceFolders = await browserBookmarkFolders();
  const targetFolders = await browserBookmarkFolders({includeEmpty: true});
  bookmarkSourceEl.innerHTML = '<option value="">All browser bookmarks</option>';
  browserRestoreTargetFolderEl.innerHTML = '<option value="">Choose a browser folder</option>';
  for (const folder of sourceFolders) {
    const option = document.createElement("option");
    option.value = folder.id;
    option.textContent = `${folder.path} (${folder.count})`;
    bookmarkSourceEl.append(option);
  }
  for (const folder of targetFolders) {
    const targetOption = document.createElement("option");
    targetOption.value = folder.id;
    targetOption.textContent = `${folder.path} (${folder.count})`;
    browserRestoreTargetFolderEl.append(targetOption);
  }
  if ([...bookmarkSourceEl.options].some((option) => option.value === currentValue)) {
    bookmarkSourceEl.value = currentValue;
  }
  if ([...browserRestoreTargetFolderEl.options].some((option) => option.value === targetValue)) {
    browserRestoreTargetFolderEl.value = targetValue;
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

function selectedBrowserRestoreOptions() {
  return {
    targetMode: browserRestoreTargetModeEl.value,
    targetFolderId: browserRestoreTargetFolderEl.value,
    targetTitle: browserRestoreFolderNameEl.value,
    duplicateAction: browserRestoreDuplicatesEl.value,
    filters: {
      query: linkvaultExportQueryEl.value,
      collection: linkvaultExportCollectionEl.value,
      favorite: linkvaultExportFavoriteEl.checked,
      pinned: linkvaultExportPinnedEl.checked,
      status: "active"
    }
  };
}

function browserRestoreOptionsKey(options) {
  return JSON.stringify({
    targetMode: options.targetMode,
    targetFolderId: options.targetFolderId,
    targetTitle: options.targetTitle,
    duplicateAction: options.duplicateAction,
    filters: options.filters
  });
}

function summarizeBrowserRestorePreview(payload) {
  return `${payload.total} from LinkVault, ${payload.create} new, ${payload.skip_existing} skipped, ${payload.merge_existing} merged, ${payload.update_existing} updated, ${payload.conflict_count || 0} conflicts, ${payload.decision_count || 0} decided.`;
}

function renderBrowserRestorePreview(payload) {
  previewDetailsEl.replaceChildren();
  previewDetailsEl.hidden = false;

  const heading = document.createElement("h2");
  heading.textContent = "Browser restore preview";
  previewDetailsEl.append(heading);

  const note = document.createElement("p");
  note.className = "muted";
  note.textContent = "No browser bookmark will be deleted. Review rows and choose skip, merge, or update for each conflict before running restore.";
  previewDetailsEl.append(note);

  const records = (payload.records || []).slice(0, PREVIEW_DETAIL_LIMIT);
  const list = document.createElement("div");
  list.className = "preview-list";
  for (const record of records) {
    list.append(browserRestorePreviewRow(record));
  }
  previewDetailsEl.append(list);
}

function browserRestorePreviewRow(record) {
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
    `target path: ${(record.path || []).join(" / ") || "-"}`,
    `source: ${record.source_folder_path || record.source_root || "-"}`
  ].join(" - ");

  row.append(header, url, meta);

  if (record.existing_bookmark) {
    const duplicate = document.createElement("p");
    duplicate.className = "muted";
    duplicate.textContent = `Existing browser bookmark: ${record.existing_bookmark.title || record.existing_bookmark.url} (${record.existing_bookmark.folder_path || "-"})`;
    row.append(duplicate);

    const decisionLabel = document.createElement("label");
    decisionLabel.textContent = "Conflict decision";
    const decisionSelect = document.createElement("select");
    decisionSelect.className = "preview-decision";
    for (const optionValue of record.available_actions || ["skip_existing", "merge_existing", "update_existing"]) {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = previewActionLabel(optionValue);
      option.selected = optionValue === record.action;
      decisionSelect.append(option);
    }
    decisionSelect.addEventListener("change", async () => {
      try {
        record.action = decisionSelect.value;
        if (record.id) {
          lastBrowserRestoreDecisions[record.id] = decisionSelect.value;
        }
        if (record.conflict_id) {
          await setConflictDecision(record.conflict_id, decisionSelect.value);
        }
        showResult(`Decision updated: ${record.title || record.url}`, "ok");
      } catch (error) {
        showResult(error.message, "error");
      }
    });
    decisionLabel.append(decisionSelect);
    row.append(decisionLabel);
  }

  return row;
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

document.querySelector("#import-into-browser").addEventListener("click", async () => {
  try {
    showResult("Restoring LinkVault bookmarks into this browser...");
    const options = selectedBrowserRestoreOptions();
    if (options.targetMode === "existing" && !options.targetFolderId) {
      throw new Error("Choose an existing browser folder or switch target to new folder.");
    }
    const result = await importLinkVaultIntoBrowser({
      ...options,
      preview: lastBrowserRestorePreviewKey === browserRestoreOptionsKey(options) ? lastBrowserRestorePreview : null
    });
    lastBrowserRestorePreview = null;
    lastBrowserRestorePreviewKey = "";
    lastBrowserRestoreDecisions = {};
    showResult(`${result.created} created, ${result.skipped_existing} skipped, ${result.merged_existing} merged, ${result.updated_existing} updated in ${result.root_title}.`, "ok");
  } catch (error) {
    showResult(error.message, "error");
  }
});

document.querySelector("#preview-browser-restore").addEventListener("click", async () => {
  try {
    showResult("Building browser restore preview...");
    const options = selectedBrowserRestoreOptions();
    lastBrowserRestorePreview = await previewLinkVaultBrowserImport({
      ...options,
      decisions: lastBrowserRestoreDecisions
    });
    lastBrowserRestorePreviewKey = browserRestoreOptionsKey(options);
    showResult(summarizeBrowserRestorePreview(lastBrowserRestorePreview), "ok");
    renderBrowserRestorePreview(lastBrowserRestorePreview);
  } catch (error) {
    lastBrowserRestorePreview = null;
    lastBrowserRestorePreviewKey = "";
    clearPreviewDetails();
    showResult(error.message, "error");
  }
});

refreshConnectionState();
refreshBookmarkSources().catch((error) => showResult(error.message, "error"));

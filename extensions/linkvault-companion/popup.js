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
const saveTabPreflightEl = document.querySelector("#save-tab-preflight");
const restoreNewFolderLabel = document.querySelector("#restore-new-folder-label");
const restoreExistingFolderLabel = document.querySelector("#restore-existing-folder-label");
const PREVIEW_DETAIL_LIMIT = 15;
let lastBrowserRestorePreview = null;
let lastBrowserRestorePreviewKey = "";
let lastBrowserRestoreDecisions = {};

function setButtonLoading(btn, loading, loadingText) {
  btn.disabled = loading;
  if (loading) {
    btn.dataset.originalText = btn.textContent;
    btn.textContent = loadingText || "Loading…";
  } else {
    btn.textContent = btn.dataset.originalText || btn.textContent;
  }
}

function updateRestoreTargetVisibility() {
  const isNew = browserRestoreTargetModeEl.value === "new";
  restoreNewFolderLabel.hidden = !isNew;
  restoreExistingFolderLabel.hidden = isNew;
}

browserRestoreTargetModeEl.addEventListener("change", updateRestoreTargetVisibility);
updateRestoreTargetVisibility();

function showResult(message, kind = "info") {
  resultEl.textContent = message;
  resultEl.className = `status ${kind}`;
}

function summarizePreview(payload) {
  const parts = [
    `${payload.total} found`,
    `${payload.create} new`,
    `${payload.duplicate_existing} already in LinkVault`,
  ];
  if (payload.duplicate_in_import) parts.push(`${payload.duplicate_in_import} duplicates in browser`);
  if (payload.invalid_skipped) parts.push(`${payload.invalid_skipped} skipped (internal)`);
  return parts.join(" · ");
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
    merge_existing: "Merge metadata",
    folder_create: "Create folder",
    reuse_existing_folder: "Reuse existing folder",
    folder_create_parallel: "Create parallel folder"
  }[action] || action || "Unknown";
}

async function refreshConnectionState() {
  const settings = await getSettings();
  if (!settings.linkvaultUrl || !settings.apiToken) {
    connectionState.textContent = "Open Options to add LinkVault URL and API token.";
    connectionState.className = "conn-state conn-missing";
    return;
  }
  connectionState.textContent = `Connecting to ${settings.linkvaultUrl}…`;
  connectionState.className = "conn-state muted";
  try {
    await linkvaultRequest("/api/me");
    connectionState.textContent = `✓ ${settings.linkvaultUrl}`;
    connectionState.className = "conn-state conn-ok";
  } catch (error) {
    connectionState.textContent = `✗ Cannot connect — check Options`;
    connectionState.className = "conn-state conn-error";
  }
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
  const parts = [
    `${payload.total} from LinkVault`,
    `${payload.create} new`,
    `${payload.skip_existing} skip`,
    `${payload.merge_existing} merge`,
    `${payload.update_existing} update`,
  ];
  if (payload.conflict_count) parts.push(`${payload.conflict_count} conflicts`);
  if (payload.structure_conflict_count) parts.push(`${payload.structure_conflict_count} folder conflicts`);
  return parts.join(" · ");
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

  const folderRecords = (payload.folder_records || []).slice(0, PREVIEW_DETAIL_LIMIT);
  if (folderRecords.length) {
    const folderHeading = document.createElement("h3");
    folderHeading.textContent = "Folder and structure conflicts";
    previewDetailsEl.append(folderHeading);

    const folderList = document.createElement("div");
    folderList.className = "preview-list";
    for (const record of folderRecords) {
      folderList.append(browserRestoreFolderPreviewRow(record));
    }
    previewDetailsEl.append(folderList);
  }

  const bookmarkHeading = document.createElement("h3");
  bookmarkHeading.textContent = "Bookmark decisions";
  previewDetailsEl.append(bookmarkHeading);

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
    `target path: ${(record.resolved_browser_path || record.path || []).join(" / ") || "-"}`,
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

function browserRestoreFolderPreviewRow(record) {
  const row = document.createElement("article");
  row.className = `preview-row ${record.action || ""}`;

  const title = document.createElement("strong");
  title.textContent = record.title || "Folder";

  const action = document.createElement("span");
  action.className = "pill";
  action.textContent = previewActionLabel(record.action);

  const header = document.createElement("div");
  header.className = "preview-row-header";
  header.append(title, action);

  const meta = document.createElement("p");
  meta.className = "muted";
  meta.textContent = [
    `source: ${record.source_path || "-"}`,
    `target folder: ${record.target_parent_path || "(root)"}`,
    `planned path: ${record.resolved_path_text || record.target_path || "-"}`
  ].join(" - ");

  row.append(header, meta);

  if (record.existing_folder) {
    const duplicate = document.createElement("p");
    duplicate.className = "muted";
    duplicate.textContent = `Existing browser folder: ${record.existing_folder.path || record.existing_folder.title || "-"}`;
    row.append(duplicate);
  }

  const decisionLabel = document.createElement("label");
  decisionLabel.textContent = "Folder decision";
  const decisionSelect = document.createElement("select");
  decisionSelect.className = "preview-decision";
  for (const optionValue of record.available_actions || ["reuse_existing_folder", "folder_create_parallel"]) {
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
      showResult(`Folder decision updated: ${record.title}`, "ok");
    } catch (error) {
      showResult(error.message, "error");
    }
  });
  decisionLabel.append(decisionSelect);
  row.append(decisionLabel);

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
  const btn = document.querySelector("#save-current-tab");
  saveTabPreflightEl.hidden = true;
  saveTabPreflightEl.replaceChildren();
  try {
    clearPreviewDetails();
    setButtonLoading(btn, true, "Saving…");
    const extra = {
      tags: document.querySelector("#save-tags").value,
      collections: document.querySelector("#save-collections").value,
      notes: document.querySelector("#save-notes").value,
      favorite: document.querySelector("#save-favorite").checked,
      pinned: document.querySelector("#save-pinned").checked
    };
    const bookmark = await saveCurrentTab(extra);
    showResult(`✓ Saved: ${bookmark.title || bookmark.url}`, "ok");
  } catch (error) {
    if (error.status === 409 && error.payload?.preflight?.matches?.length) {
      renderSaveTabPreflight(error.payload.preflight, {
        tags: document.querySelector("#save-tags").value,
        collections: document.querySelector("#save-collections").value,
        notes: document.querySelector("#save-notes").value,
        favorite: document.querySelector("#save-favorite").checked,
        pinned: document.querySelector("#save-pinned").checked
      });
      showResult("Already in LinkVault — choose an action below.", "info");
    } else {
      showResult(error.message, "error");
    }
  } finally {
    setButtonLoading(btn, false);
  }
});

function renderSaveTabPreflight(preflight, extra) {
  saveTabPreflightEl.hidden = false;
  saveTabPreflightEl.replaceChildren();

  const heading = document.createElement("p");
  heading.className = "preflight-heading";
  heading.textContent = "Already saved — what would you like to do?";
  saveTabPreflightEl.append(heading);

  for (const match of preflight.matches || []) {
    const bm = match.bookmark;
    const row = document.createElement("div");
    row.className = "preflight-match";

    const matchType = document.createElement("span");
    matchType.className = "pill pill-warn";
    matchType.textContent = match.match_type === "exact" ? "Exact match" : match.match_type === "normalized" ? "Normalized match" : "Similar";
    row.append(matchType);

    const title = document.createElement("strong");
    title.textContent = ` ${bm.title || bm.url}`;
    row.append(title);

    const btnRow = document.createElement("div");
    btnRow.className = "actions";

    const openBtn = document.createElement("button");
    openBtn.textContent = "Open in LinkVault";
    openBtn.type = "button";
    openBtn.addEventListener("click", async () => {
      const settings = await getSettings();
      linkvaultRuntime.tabs.create({url: `${settings.linkvaultUrl}/#bookmark-${bm.id}`});
    });
    btnRow.append(openBtn);

    const saveAnywayBtn = document.createElement("button");
    saveAnywayBtn.textContent = "Save anyway";
    saveAnywayBtn.type = "button";
    saveAnywayBtn.addEventListener("click", async () => {
      try {
        setButtonLoading(saveAnywayBtn, true, "Saving…");
        const payload = await currentTabBookmarkPayload(extra);
        payload.allow_duplicate = true;
        const saved = await linkvaultRequest("/api/bookmarks", {
          method: "POST",
          body: JSON.stringify(payload)
        });
        saveTabPreflightEl.hidden = true;
        showResult(`✓ Saved as new bookmark: ${saved.title || saved.url}`, "ok");
      } catch (err) {
        showResult(err.message, "error");
      } finally {
        setButtonLoading(saveAnywayBtn, false);
      }
    });
    btnRow.append(saveAnywayBtn);
    row.append(btnRow);
    saveTabPreflightEl.append(row);
  }
}

document.querySelector("#preview-bookmarks").addEventListener("click", async () => {
  const btn = document.querySelector("#preview-bookmarks");
  try {
    setButtonLoading(btn, true, "Previewing…");
    showResult("Reading browser bookmarks…");
    const preview = await previewBrowserBookmarks(selectedBookmarkSource());
    showResult(summarizePreview(preview), "ok");
    renderPreviewDetails(preview);
  } catch (error) {
    clearPreviewDetails();
    showResult(error.message, "error");
  } finally {
    setButtonLoading(btn, false);
  }
});

document.querySelector("#import-bookmarks").addEventListener("click", async () => {
  const btn = document.querySelector("#import-bookmarks");
  try {
    setButtonLoading(btn, true, "Importing…");
    showResult("Importing browser bookmarks…");
    const result = await importBrowserBookmarks(selectedBookmarkSource());
    const invalid = result.invalid_skipped ? `, ${result.invalid_skipped} skipped` : "";
    showResult(`✓ ${result.created} new bookmarks imported. ${result.duplicates_skipped} already existed${invalid}.`, "ok");
    clearPreviewDetails();
  } catch (error) {
    showResult(error.message, "error");
  } finally {
    setButtonLoading(btn, false);
  }
});

document.querySelector("#import-into-browser").addEventListener("click", async () => {
  const btn = document.querySelector("#import-into-browser");
  try {
    const options = selectedBrowserRestoreOptions();
    if (options.targetMode === "existing" && !options.targetFolderId) {
      showResult("Choose an existing browser folder, or switch target to 'Create new folder'.", "error");
      return;
    }
    if (!lastBrowserRestorePreview) {
      showResult("Preview the restore plan first before applying.", "error");
      return;
    }
    const totalNew = lastBrowserRestorePreview.create || 0;
    if (totalNew > 30 && !confirm(`This will create ${totalNew} new browser bookmarks. Continue?`)) {
      return;
    }
    setButtonLoading(btn, true, "Applying…");
    showResult("Restoring LinkVault bookmarks into this browser…");
    const result = await importLinkVaultIntoBrowser({
      ...options,
      preview: lastBrowserRestorePreviewKey === browserRestoreOptionsKey(options) ? lastBrowserRestorePreview : null
    });
    lastBrowserRestorePreview = null;
    lastBrowserRestorePreviewKey = "";
    lastBrowserRestoreDecisions = {};
    clearPreviewDetails();
    const syncNote = result.restore_session_sync_failed ? ` (Session sync failed: ${result.restore_session_sync_error}.)` : "";
    showResult(`✓ ${result.created} created, ${result.skipped_existing} skipped, ${result.merged_existing} merged, ${result.updated_existing} updated in "${result.root_title}".${syncNote}`, result.restore_session_sync_failed ? "error" : "ok");
  } catch (error) {
    showResult(error.message, "error");
  } finally {
    setButtonLoading(btn, false);
  }
});

document.querySelector("#preview-browser-restore").addEventListener("click", async () => {
  const btn = document.querySelector("#preview-browser-restore");
  try {
    setButtonLoading(btn, true, "Building preview…");
    showResult("Building browser restore preview…");
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
  } finally {
    setButtonLoading(btn, false);
  }
});

refreshConnectionState();
refreshBookmarkSources().catch((error) => showResult(error.message, "error"));

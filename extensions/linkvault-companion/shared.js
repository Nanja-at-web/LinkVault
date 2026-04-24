const linkvaultRuntime = globalThis.browser || globalThis.chrome;

function storageGet(keys) {
  if (globalThis.browser?.storage?.local) {
    return globalThis.browser.storage.local.get(keys);
  }
  return new Promise((resolve) => {
    linkvaultRuntime.storage.local.get(keys, resolve);
  });
}

function storageSet(values) {
  if (globalThis.browser?.storage?.local) {
    return globalThis.browser.storage.local.set(values);
  }
  return new Promise((resolve) => {
    linkvaultRuntime.storage.local.set(values, resolve);
  });
}

function queryTabs(query) {
  if (globalThis.browser?.tabs) {
    return globalThis.browser.tabs.query(query);
  }
  return new Promise((resolve) => {
    linkvaultRuntime.tabs.query(query, resolve);
  });
}

function getBookmarkTree() {
  if (globalThis.browser?.bookmarks) {
    return globalThis.browser.bookmarks.getTree();
  }
  return new Promise((resolve) => {
    linkvaultRuntime.bookmarks.getTree(resolve);
  });
}

function getBookmarkSubTree(id) {
  if (globalThis.browser?.bookmarks) {
    return globalThis.browser.bookmarks.getSubTree(id);
  }
  return new Promise((resolve) => {
    linkvaultRuntime.bookmarks.getSubTree(id, resolve);
  });
}

function createBrowserBookmark(payload) {
  if (globalThis.browser?.bookmarks) {
    return globalThis.browser.bookmarks.create(payload);
  }
  return new Promise((resolve) => {
    linkvaultRuntime.bookmarks.create(payload, resolve);
  });
}

function updateBrowserBookmark(id, changes) {
  if (globalThis.browser?.bookmarks) {
    return globalThis.browser.bookmarks.update(id, changes);
  }
  return new Promise((resolve) => {
    linkvaultRuntime.bookmarks.update(id, changes, resolve);
  });
}

function moveBrowserBookmark(id, destination) {
  if (globalThis.browser?.bookmarks) {
    return globalThis.browser.bookmarks.move(id, destination);
  }
  return new Promise((resolve) => {
    linkvaultRuntime.bookmarks.move(id, destination, resolve);
  });
}

function requestPermissions(permissions) {
  if (!linkvaultRuntime.permissions?.request) {
    return Promise.resolve(true);
  }
  if (globalThis.browser?.permissions) {
    return globalThis.browser.permissions.request(permissions);
  }
  return new Promise((resolve) => {
    linkvaultRuntime.permissions.request(permissions, resolve);
  });
}

async function getSettings() {
  const settings = await storageGet(["linkvaultUrl", "apiToken"]);
  return {
    linkvaultUrl: normalizeBaseUrl(settings.linkvaultUrl || ""),
    apiToken: settings.apiToken || ""
  };
}

function normalizeBaseUrl(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

async function requestLinkVaultHostPermission(baseUrl) {
  const pattern = hostPermissionPattern(baseUrl);
  if (!pattern) return true;
  return requestPermissions({origins: [pattern]});
}

function hostPermissionPattern(baseUrl) {
  try {
    const parsed = new URL(baseUrl);
    if (!["http:", "https:"].includes(parsed.protocol)) return "";
    return `${parsed.protocol}//${parsed.hostname}/*`;
  } catch (error) {
    return "";
  }
}

async function linkvaultRequest(path, options = {}) {
  const settings = await getSettings();
  if (!settings.linkvaultUrl || !settings.apiToken) {
    throw new Error("LinkVault URL and API token are required.");
  }

  const response = await fetch(`${settings.linkvaultUrl}${path}`, {
    ...options,
    headers: {
      "content-type": "application/json",
      "authorization": `Bearer ${settings.apiToken}`,
      ...(options.headers || {})
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.error === "url host is required"
      ? "LinkVault rejected a bookmark with an invalid URL. Internal browser URLs are skipped in the latest extension; reload the extension and try again."
      : payload.error || `LinkVault request failed with ${response.status}.`;
    const error = new Error(message);
    error.payload = payload;
    error.status = response.status;
    throw error;
  }
  return payload;
}

async function testLinkVaultConnection() {
  const settings = await getSettings();
  if (!settings.linkvaultUrl) {
    throw new Error("LinkVault URL is required.");
  }
  let response;
  try {
    response = await fetch(`${settings.linkvaultUrl}/healthz`, {
      method: "GET",
      cache: "no-store"
    });
  } catch (error) {
    await diagnoseReachability(settings.linkvaultUrl);
    throw new Error(
      `Cannot reach LinkVault at ${settings.linkvaultUrl}. Open ${settings.linkvaultUrl}/healthz in a normal browser tab. If it works there, reload the extension and check host permissions.`
    );
  }
  if (!response.ok) {
    throw new Error(`Healthcheck failed with ${response.status}.`);
  }
  return response.json();
}

async function discoverLinkVaultServers(options = {}) {
  const candidates = await linkvaultDiscoveryCandidates(options);
  const checks = await mapWithConcurrency(candidates, 12, probeLinkVaultServer);
  const results = checks.filter(Boolean);
  const seen = new Set();
  return results.filter((result) => {
    if (seen.has(result.url)) return false;
    seen.add(result.url);
    return true;
  });
}

async function linkvaultDiscoveryCandidates(options = {}) {
  const candidates = [];
  const inputUrl = normalizeBaseUrl(options.inputUrl || "");
  const settings = await getSettings();
  const storedUrl = normalizeBaseUrl(settings.linkvaultUrl || "");

  appendDiscoveryCandidate(candidates, inputUrl, "Current form value");
  appendDiscoveryCandidate(candidates, storedUrl, "Saved setting");

  const tabs = await queryTabs({});
  for (const tab of tabs || []) {
    appendDiscoveryCandidate(candidates, candidateBaseUrlFromPage(tab.url), "Open browser tab");
  }

  appendDiscoveryCandidate(candidates, "http://linkvault.local:3080", "Local hostname");
  appendDiscoveryCandidate(candidates, "http://linkvault:3080", "Local hostname");

  if (options.includeSubnet) {
    const subnetPrefix = String(options.subnetPrefix || "").trim();
    if (/^(?:\d{1,3}\.){2}\d{1,3}$/.test(subnetPrefix)) {
      for (let host = 1; host <= 254; host += 1) {
        appendDiscoveryCandidate(candidates, `http://${subnetPrefix}.${host}:3080`, "Subnet scan");
      }
    }
  }

  const seen = new Set();
  return candidates.filter((candidate) => {
    if (!candidate.url || seen.has(candidate.url)) return false;
    seen.add(candidate.url);
    return true;
  });
}

function appendDiscoveryCandidate(candidates, url, source) {
  const normalized = normalizeBaseUrl(url || "");
  if (!normalized) return;
  try {
    const parsed = new URL(normalized);
    if (!["http:", "https:"].includes(parsed.protocol)) return;
    candidates.push({url: parsed.origin, source});
  } catch (error) {
    return;
  }
}

function candidateBaseUrlFromPage(value) {
  try {
    const parsed = new URL(value || "");
    if (!["http:", "https:"].includes(parsed.protocol)) return "";
    return parsed.origin;
  } catch (error) {
    return "";
  }
}

async function probeLinkVaultServer(candidate) {
  const identity = await fetchJsonWithTimeout(`${candidate.url}/.well-known/linkvault`, 900);
  if (identity && identity.app === "LinkVault") {
    return {
      url: candidate.url,
      source: candidate.source,
      version: identity.version || ""
    };
  }

  const health = await fetchJsonWithTimeout(`${candidate.url}/healthz`, 900);
  if (health?.ok && health.version) {
    return {
      url: candidate.url,
      source: candidate.source,
      version: health.version || ""
    };
  }

  return null;
}

async function fetchJsonWithTimeout(url, timeoutMs = 900) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal
    });
    if (!response.ok) return null;
    return await response.json().catch(() => null);
  } catch (error) {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

async function mapWithConcurrency(items, concurrency, worker) {
  const results = [];
  let index = 0;
  const workers = Array.from({length: Math.min(concurrency, items.length)}, async () => {
    while (index < items.length) {
      const currentIndex = index;
      index += 1;
      results[currentIndex] = await worker(items[currentIndex]);
    }
  });
  await Promise.all(workers);
  return results;
}

async function diagnoseReachability(baseUrl) {
  try {
    await fetch(`${baseUrl}/healthz`, {
      method: "GET",
      mode: "no-cors",
      cache: "no-store"
    });
  } catch (error) {
    throw new Error(
      `Network cannot reach ${baseUrl}/healthz from the extension. Check the IP address, LXC status, firewall, and whether the browser can open the health URL directly.`
    );
  }
}

async function currentTabBookmarkPayload(extra = {}) {
  const [tab] = await queryTabs({active: true, currentWindow: true});
  if (!tab?.url || !/^https?:\/\//i.test(tab.url)) {
    throw new Error("Current tab is not a regular HTTP/HTTPS page.");
  }
  return {
    url: tab.url,
    title: tab.title || tab.url,
    tags: splitCommaValues(extra.tags || "browser"),
    collections: splitCommaValues(extra.collections || "Inbox"),
    notes: extra.notes || "",
    favorite: Boolean(extra.favorite),
    pinned: Boolean(extra.pinned)
  };
}

async function saveCurrentTab(extra = {}) {
  const payload = await currentTabBookmarkPayload(extra);
  return linkvaultRequest("/api/bookmarks", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

async function previewBrowserBookmarks(options = {}) {
  const items = await browserBookmarksToItems(options);
  return linkvaultRequest("/api/import/browser-bookmarks/preview", {
    method: "POST",
    body: JSON.stringify({items})
  });
}

async function importBrowserBookmarks(options = {}) {
  const items = await browserBookmarksToItems(options);
  return linkvaultRequest("/api/import/browser-bookmarks", {
    method: "POST",
    body: JSON.stringify({items})
  });
}

async function browserBookmarksToItems(options = {}) {
  const tree = options.rootId ? await getBookmarkSubTree(options.rootId) : await getBookmarkTree();
  const filters = normalizeBookmarkFilters(options.filters || {});
  const items = [];
  for (const node of tree) {
    appendBookmarkItem(items, node, {
      isRoot: !options.rootId,
      path: [],
      filters,
      sourceRoot: "",
      sourceBrowser: browserSourceName()
    });
  }
  return items;
}

async function browserBookmarksToNetscapeHtml(options = {}) {
  const tree = options.rootId ? await getBookmarkSubTree(options.rootId) : await getBookmarkTree();
  const filters = normalizeBookmarkFilters(options.filters || {});
  const lines = [
    "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
    '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
    "<TITLE>Bookmarks</TITLE>",
    "<H1>Bookmarks</H1>",
    "<DL><p>"
  ];
  for (const node of tree) {
    appendBookmarkNode(lines, node, 1, !options.rootId, [], filters);
  }
  lines.push("</DL><p>");
  return lines.join("\n");
}

async function linkvaultBrowserExport(options = {}) {
  const query = new URLSearchParams();
  const filters = options.filters || {};
  if (filters.query) query.set("q", filters.query);
  if (filters.collection) query.set("collection", filters.collection);
  if (filters.favorite) query.set("favorite", "1");
  if (filters.pinned) query.set("pinned", "1");
  if (filters.status) query.set("status", filters.status);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return linkvaultRequest(`/api/export/browser-bookmarks${suffix}`);
}

async function previewLinkVaultBrowserImport(options = {}) {
  const existingItems = options.existingItems || await browserExistingItems();
  const existingFolders = options.existingFolders || await browserExistingFolders();
  return linkvaultRequest("/api/export/browser-bookmarks/restore-preview", {
    method: "POST",
    body: JSON.stringify({
      query: options.filters?.query || "",
      filters: options.filters || {},
      existing_items: existingItems,
      existing_folders: existingFolders,
      duplicate_action: options.duplicateAction || "skip",
      target_mode: options.targetMode || "new",
      target_folder_id: options.targetFolderId || "",
      target_title: options.targetTitle || "",
      decisions: options.decisions || {}
    })
  });
}

async function completeLinkVaultBrowserRestore(sessionId, result = {}) {
  return linkvaultRequest("/api/export/browser-bookmarks/restore-complete", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      created: Number(result.created || 0),
      skipped_existing: Number(result.skipped_existing || 0),
      merged_existing: Number(result.merged_existing || 0),
      updated_existing: Number(result.updated_existing || 0),
      root_title: result.root_title || "",
      status: result.status || "completed"
    })
  });
}

async function importLinkVaultIntoBrowser(options = {}) {
  const preview = options.preview || await previewLinkVaultBrowserImport(options);
  const target = await resolveBrowserRestoreTarget(options, preview);
  const folderCache = new Map();
  const existingIndex = await browserBookmarkUrlIndex();
  let created = 0;
  let skipped = 0;
  let updated = 0;
  let merged = 0;

  for (const record of preview.records || []) {
    if (!isRegularWebUrl(record.url)) continue;
    const existing = existingIndex.get(comparableBookmarkUrl(record.url));
    const action = record.action || preview.duplicate_action || "skip_existing";
    if (existing) {
      if (action === "update_existing") {
        const parentId = await ensureBrowserFolderPath(target.id, record.resolved_path || restorePathForTarget(record.path, target, options), folderCache);
        await updateBrowserBookmark(existing.id, {title: record.title || existing.title || record.url});
        await moveBrowserBookmark(existing.id, {parentId});
        updated += 1;
      } else if (action === "merge_existing") {
        await updateBrowserBookmark(existing.id, {title: record.title || existing.title || record.url});
        merged += 1;
      } else {
        skipped += 1;
      }
      continue;
    }

    const parentId = await ensureBrowserFolderPath(target.id, record.resolved_path || restorePathForTarget(record.path, target, options), folderCache);
    await createBrowserBookmark({
      parentId,
      title: record.title || record.url,
      url: record.url
    });
    created += 1;
  }

  const result = {
    session_id: preview.session_id || preview.preview_id || "",
    root_title: target.title,
    created,
    skipped_existing: skipped,
    updated_existing: updated,
    merged_existing: merged,
    bookmark_count: preview.total || created
  };

  if (result.session_id) {
    try {
      result.restore_session = await completeLinkVaultBrowserRestore(result.session_id, result);
    } catch (error) {
      result.restore_session_sync_failed = true;
      result.restore_session_sync_error = error.message || String(error);
    }
  };

  return result;
}

function restorePathForTarget(path, target, options = {}) {
  const cleanPath = (path || []).filter(Boolean);
  if (options.targetMode !== "existing" || !cleanPath.length) return cleanPath;
  const targetTitle = String(target.title || "").trim().toLowerCase();
  if (targetTitle && cleanPath[0].trim().toLowerCase() === targetTitle) {
    return cleanPath.slice(1);
  }
  return cleanPath;
}

async function resolveBrowserRestoreTarget(options, preview) {
  const targetRoot = preview.target_root || {};
  if (options.targetMode !== "existing" && targetRoot.reuse_existing && targetRoot.id) {
    return {
      id: targetRoot.id,
      title: targetRoot.title || "Existing LinkVault folder"
    };
  }

  if (options.targetMode === "existing" && options.targetFolderId) {
    const [folder] = await getBookmarkSubTree(options.targetFolderId);
    return {
      id: options.targetFolderId,
      title: folder?.title || "Selected browser folder"
    };
  }

  const rootTitle = String(targetRoot.title || options.targetTitle || preview.root_title || "").trim()
    || `LinkVault Restore ${new Date().toISOString().slice(0, 10)}`;
  const root = await createBrowserBookmark({title: rootTitle});
  return {id: root.id, title: rootTitle};
}

async function ensureBrowserFolderPath(rootId, path, folderCache) {
  let parentId = rootId;
  for (const title of path || []) {
    const cleanTitle = String(title || "").trim();
    if (!cleanTitle) continue;
    const cacheKey = `${parentId}\n${cleanTitle}`;
    if (folderCache.has(cacheKey)) {
      parentId = folderCache.get(cacheKey);
      continue;
    }
    const existing = await findChildFolder(parentId, cleanTitle);
    if (existing) {
      parentId = existing.id;
    } else {
      const folder = await createBrowserBookmark({parentId, title: cleanTitle});
      parentId = folder.id;
    }
    folderCache.set(cacheKey, parentId);
  }
  return parentId;
}

async function findChildFolder(parentId, title) {
  const [parent] = await getBookmarkSubTree(parentId);
  const children = Array.isArray(parent?.children) ? parent.children : [];
  return children.find((child) => !child.url && child.title === title) || null;
}

function flattenLinkVaultExportTree(exportTree) {
  const records = [];
  for (const root of exportTree.roots || []) {
    appendExportTreeRecord(records, root, []);
  }
  return records;
}

function appendExportTreeRecord(records, node, path) {
  if (node.type === "bookmark" || node.url) {
    if (!isRegularWebUrl(node.url)) return;
    records.push({
      title: node.title || node.url,
      url: node.url,
      tags: node.tags || [],
      collections: node.collections || [],
      path,
      source_root: node.source_root || "",
      source_folder_path: node.source_folder_path || path.join(" / "),
      source_position: Number.isFinite(Number(node.source_position)) ? Number(node.source_position) : records.length
    });
    return;
  }

  const title = String(node.title || "").trim();
  const nextPath = title ? [...path, title] : path;
  for (const child of node.children || []) {
    appendExportTreeRecord(records, child, nextPath);
  }
}

async function browserBookmarkUrlIndex() {
  const tree = await getBookmarkTree();
  const index = new Map();
  for (const root of tree) {
    appendBrowserBookmarkIndex(index, root, []);
  }
  return index;
}

function appendBrowserBookmarkIndex(index, node, path) {
  if (node.url) {
    if (!isRegularWebUrl(node.url)) return;
    const key = comparableBookmarkUrl(node.url);
    if (!index.has(key)) {
      index.set(key, {
        id: node.id,
        title: node.title || node.url,
        url: node.url,
        folder_path: path.join(" / ")
      });
    }
    return;
  }

  const title = String(node.title || "").trim();
  const nextPath = title ? [...path, title] : path;
  for (const child of node.children || []) {
    appendBrowserBookmarkIndex(index, child, nextPath);
  }
}

async function browserExistingItems() {
  const index = await browserBookmarkUrlIndex();
  return [...index.values()];
}

async function browserExistingFolders() {
  const tree = await getBookmarkTree();
  const folders = [];
  for (const root of tree) {
    appendBrowserFolderIndex(folders, root, []);
  }
  return folders;
}

function comparableBookmarkUrl(value) {
  try {
    const parsed = new URL(value);
    parsed.hash = "";
    for (const key of [...parsed.searchParams.keys()]) {
      if (key.startsWith("utm_") || ["fbclid", "gclid", "mc_cid", "mc_eid"].includes(key)) {
        parsed.searchParams.delete(key);
      }
    }
    return parsed.toString().replace(/\/$/, "").toLowerCase();
  } catch (error) {
    return String(value || "").trim().replace(/\/$/, "").toLowerCase();
  }
}

async function setConflictDecision(conflictId, decision) {
  return linkvaultRequest(`/api/conflicts/${conflictId}/decision`, {
    method: "POST",
    body: JSON.stringify({decision})
  });
}

function appendBrowserFolderIndex(folders, node, path) {
  if (node.url) return;
  const title = String(node.title || "").trim();
  const nextPath = title ? [...path, title] : path;
  if (title) {
    folders.push({
      id: String(node.id || ""),
      title,
      path: nextPath.join(" / "),
      parent_path: path.join(" / "),
      count: countWebBookmarks(node)
    });
  }
  for (const child of node.children || []) {
    appendBrowserFolderIndex(folders, child, nextPath);
  }
}

async function browserBookmarkFolders(options = {}) {
  const tree = await getBookmarkTree();
  const folders = [];
  for (const node of tree) {
    appendBookmarkFolder(folders, node, [], Boolean(options.includeEmpty));
  }
  return options.includeEmpty ? folders : folders.filter((folder) => folder.count > 0);
}

function appendBookmarkFolder(folders, node, path, includeEmpty = false) {
  if (node.url) return countWebBookmarks(node);

  const title = String(node.title || "").trim();
  const nextPath = title ? [...path, title] : path;
  const children = Array.isArray(node.children) ? node.children : [];
  let count = 0;

  for (const child of children) {
    count += appendBookmarkFolder(folders, child, nextPath, includeEmpty);
  }

  if (title && (includeEmpty || count > 0)) {
    folders.push({
      id: node.id,
      title,
      path: nextPath.join(" / "),
      count
    });
  }

  return count;
}

function countWebBookmarks(node) {
  if (node.url) return isRegularWebUrl(node.url) ? 1 : 0;
  const children = Array.isArray(node.children) ? node.children : [];
  return children.reduce((total, child) => total + countWebBookmarks(child), 0);
}

function appendBookmarkNode(lines, node, depth, isRoot = false, path = [], filters = {}) {
  const indent = "  ".repeat(depth);
  if (node.url) {
    if (!isRegularWebUrl(node.url)) return 0;
    if (!bookmarkMatchesFilters(node, path, filters)) return 0;
    const attrs = [`HREF="${escapeAttribute(node.url)}"`];
    if (node.dateAdded) attrs.push(`ADD_DATE="${Math.floor(Number(node.dateAdded) / 1000)}"`);
    lines.push(`${indent}<DT><A ${attrs.join(" ")}>${escapeHtml(node.title || node.url)}</A>`);
    return 1;
  }

  const children = Array.isArray(node.children) ? node.children : [];
  if (!children.length) return 0;

  const title = String(node.title || "").trim();
  const nextPath = !isRoot && title ? [...path, title] : path;

  if (!isRoot && title) {
    const childLines = [];
    let count = 0;
    for (const child of children) {
      count += appendBookmarkNode(childLines, child, depth + 1, false, nextPath, filters);
    }
    if (!count) return 0;
    lines.push(`${indent}<DT><H3>${escapeHtml(title)}</H3>`);
    lines.push(`${indent}<DL><p>`);
    lines.push(...childLines);
    lines.push(`${indent}</DL><p>`);
    return count;
  }

  let count = 0;
  for (const child of children) {
    count += appendBookmarkNode(lines, child, depth, false, nextPath, filters);
  }
  return count;
}

function appendBookmarkItem(items, node, context) {
  const {isRoot, filters, sourceBrowser} = context;
  const path = context.path || [];
  const sourceRoot = context.sourceRoot || "";

  if (node.url) {
    if (!isRegularWebUrl(node.url)) return 0;
    if (!bookmarkMatchesFilters(node, path, filters)) return 0;
    items.push({
      url: node.url,
      title: node.title || node.url,
      collections: path,
      source_browser: sourceBrowser,
      source_root: sourceRoot || path[0] || "",
      source_folder_path: path.join(" / "),
      source_position: Number.isFinite(Number(node.index)) ? Number(node.index) : items.length,
      source_bookmark_id: String(node.id || "")
    });
    return 1;
  }

  const children = Array.isArray(node.children) ? node.children : [];
  if (!children.length) return 0;

  const title = String(node.title || "").trim();
  const nextPath = !isRoot && title ? [...path, title] : path;
  const nextRoot = sourceRoot || (!isRoot && title ? title : "");

  let count = 0;
  for (const child of children) {
    count += appendBookmarkItem(items, child, {
      isRoot: false,
      path: nextPath,
      filters,
      sourceRoot: nextRoot,
      sourceBrowser
    });
  }
  return count;
}

function browserSourceName() {
  const userAgent = navigator.userAgent || "";
  if (userAgent.includes("Firefox/")) return "firefox-extension";
  if (userAgent.includes("Edg/")) return "edge-extension";
  if (userAgent.includes("Chrome/")) return "chrome-extension";
  if (userAgent.includes("Safari/")) return "safari-extension";
  return "browser-extension";
}

function normalizeBookmarkFilters(filters = {}) {
  return {
    query: String(filters.query || "").trim().toLowerCase(),
    domain: String(filters.domain || "").trim().toLowerCase(),
    addedFrom: parseDateStart(filters.addedFrom),
    addedTo: parseDateEnd(filters.addedTo)
  };
}

function bookmarkMatchesFilters(node, path, filters) {
  if (filters.query) {
    const haystack = [
      node.title || "",
      node.url || "",
      path.join(" / ")
    ].join(" ").toLowerCase();
    if (!haystack.includes(filters.query)) return false;
  }

  if (filters.domain) {
    const url = String(node.url || "").toLowerCase();
    const host = urlHostname(url).toLowerCase();
    if (!url.includes(filters.domain) && !host.includes(filters.domain)) return false;
  }

  const addedAt = Number(node.dateAdded || 0);
  if (filters.addedFrom && (!addedAt || addedAt < filters.addedFrom)) return false;
  if (filters.addedTo && (!addedAt || addedAt > filters.addedTo)) return false;

  return true;
}

function parseDateStart(value) {
  if (!value) return 0;
  const parsed = new Date(`${value}T00:00:00`);
  const timestamp = parsed.getTime();
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function parseDateEnd(value) {
  if (!value) return 0;
  const parsed = new Date(`${value}T23:59:59.999`);
  const timestamp = parsed.getTime();
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function urlHostname(value) {
  try {
    return new URL(value).hostname;
  } catch (error) {
    return "";
  }
}

function splitCommaValues(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function isRegularWebUrl(value) {
  return /^https?:\/\//i.test(String(value || ""));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/`/g, "&#96;");
}

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
  const html = await browserBookmarksToNetscapeHtml(options);
  return linkvaultRequest("/api/import/browser-html/preview", {
    method: "POST",
    body: JSON.stringify({data: html})
  });
}

async function importBrowserBookmarks(options = {}) {
  const html = await browserBookmarksToNetscapeHtml(options);
  return linkvaultRequest("/api/import/browser-html", {
    method: "POST",
    body: JSON.stringify({data: html})
  });
}

async function browserBookmarksToNetscapeHtml(options = {}) {
  const tree = options.rootId ? await getBookmarkSubTree(options.rootId) : await getBookmarkTree();
  const lines = [
    "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
    '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
    "<TITLE>Bookmarks</TITLE>",
    "<H1>Bookmarks</H1>",
    "<DL><p>"
  ];
  for (const node of tree) {
    appendBookmarkNode(lines, node, 1, !options.rootId);
  }
  lines.push("</DL><p>");
  return lines.join("\n");
}

async function browserBookmarkFolders() {
  const tree = await getBookmarkTree();
  const folders = [];
  for (const node of tree) {
    appendBookmarkFolder(folders, node, []);
  }
  return folders.filter((folder) => folder.count > 0);
}

function appendBookmarkFolder(folders, node, path) {
  if (node.url) return countWebBookmarks(node);

  const title = String(node.title || "").trim();
  const nextPath = title ? [...path, title] : path;
  const children = Array.isArray(node.children) ? node.children : [];
  let count = 0;

  for (const child of children) {
    count += appendBookmarkFolder(folders, child, nextPath);
  }

  if (title && count > 0) {
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

function appendBookmarkNode(lines, node, depth, isRoot = false) {
  const indent = "  ".repeat(depth);
  if (node.url) {
    if (!isRegularWebUrl(node.url)) return;
    lines.push(`${indent}<DT><A HREF="${escapeAttribute(node.url)}">${escapeHtml(node.title || node.url)}</A>`);
    return;
  }

  const children = Array.isArray(node.children) ? node.children : [];
  if (!children.length) return;

  if (!isRoot && node.title) {
    lines.push(`${indent}<DT><H3>${escapeHtml(node.title)}</H3>`);
    lines.push(`${indent}<DL><p>`);
    for (const child of children) appendBookmarkNode(lines, child, depth + 1);
    lines.push(`${indent}</DL><p>`);
    return;
  }

  for (const child of children) appendBookmarkNode(lines, child, depth);
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

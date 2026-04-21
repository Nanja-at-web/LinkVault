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
    const error = new Error(payload.error || `LinkVault request failed with ${response.status}.`);
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

async function previewBrowserBookmarks() {
  const html = await browserBookmarksToNetscapeHtml();
  return linkvaultRequest("/api/import/browser-html/preview", {
    method: "POST",
    body: JSON.stringify({data: html})
  });
}

async function importBrowserBookmarks() {
  const html = await browserBookmarksToNetscapeHtml();
  return linkvaultRequest("/api/import/browser-html", {
    method: "POST",
    body: JSON.stringify({data: html})
  });
}

async function browserBookmarksToNetscapeHtml() {
  const tree = await getBookmarkTree();
  const lines = [
    "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
    '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
    "<TITLE>Bookmarks</TITLE>",
    "<H1>Bookmarks</H1>",
    "<DL><p>"
  ];
  for (const node of tree) {
    appendBookmarkNode(lines, node, 1, true);
  }
  lines.push("</DL><p>");
  return lines.join("\n");
}

function appendBookmarkNode(lines, node, depth, isRoot = false) {
  const indent = "  ".repeat(depth);
  if (node.url) {
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

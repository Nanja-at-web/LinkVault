const optionsForm = document.querySelector("#options-form");
const statusEl = document.querySelector("#status");
const discoveryResultsEl = document.querySelector("#discovery-results");
const subnetPrefixEl = document.querySelector("#subnet-prefix");

async function loadOptions() {
  const settings = await getSettings();
  optionsForm.elements.linkvaultUrl.value = settings.linkvaultUrl;
  optionsForm.elements.apiToken.value = settings.apiToken;
  subnetPrefixEl.value = subnetPrefixFromUrl(settings.linkvaultUrl) || subnetPrefixEl.value;
}

function showStatus(message, kind = "info") {
  statusEl.textContent = message;
  statusEl.className = `status ${kind}`;
}

function renderDiscoveryResults(results) {
  discoveryResultsEl.replaceChildren();
  discoveryResultsEl.hidden = false;

  if (!results.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No LinkVault server found.";
    discoveryResultsEl.append(empty);
    return;
  }

  for (const result of results) {
    const row = document.createElement("article");
    row.className = "discovery-row";

    const title = document.createElement("strong");
    title.textContent = result.url;

    const meta = document.createElement("p");
    meta.className = "muted";
    meta.textContent = `${result.source} - LinkVault ${result.version || "unknown version"}`;

    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Use this instance";
    button.addEventListener("click", () => {
      optionsForm.elements.linkvaultUrl.value = result.url;
      subnetPrefixEl.value = subnetPrefixFromUrl(result.url) || subnetPrefixEl.value;
      showStatus(`Selected ${result.url}. Save settings to keep it.`, "ok");
    });

    row.append(title, meta, button);
    discoveryResultsEl.append(row);
  }
}

optionsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  await storageSet({
    linkvaultUrl: normalizeBaseUrl(data.linkvaultUrl),
    apiToken: data.apiToken.trim()
  });
  showStatus("Settings saved.", "ok");
});

document.querySelector("#find-linkvault").addEventListener("click", async () => {
  try {
    showStatus("Searching likely LinkVault addresses...");
    const data = Object.fromEntries(new FormData(optionsForm));
    const results = await discoverLinkVaultServers({
      inputUrl: data.linkvaultUrl,
      includeSubnet: false
    });
    renderDiscoveryResults(results);
    showStatus(results.length ? `${results.length} LinkVault server found.` : "No LinkVault server found.", results.length ? "ok" : "info");
  } catch (error) {
    showStatus(error.message, "error");
  }
});

document.querySelector("#scan-subnet").addEventListener("click", async () => {
  try {
    const subnetPrefix = subnetPrefixEl.value.trim();
    if (!/^(?:\d{1,3}\.){2}\d{1,3}$/.test(subnetPrefix)) {
      showStatus("Subnet prefix must look like 192.168.1.", "error");
      return;
    }
    showStatus(`Scanning ${subnetPrefix}.1-254 on port 3080...`);
    const data = Object.fromEntries(new FormData(optionsForm));
    const results = await discoverLinkVaultServers({
      inputUrl: data.linkvaultUrl,
      includeSubnet: true,
      subnetPrefix
    });
    renderDiscoveryResults(results);
    showStatus(results.length ? `${results.length} LinkVault server found.` : "No LinkVault server found in subnet.", results.length ? "ok" : "info");
  } catch (error) {
    showStatus(error.message, "error");
  }
});

document.querySelector("#test-connection").addEventListener("click", async () => {
  try {
    const data = Object.fromEntries(new FormData(optionsForm));
    const linkvaultUrl = normalizeBaseUrl(data.linkvaultUrl);
    const granted = await requestLinkVaultHostPermission(linkvaultUrl);
    if (!granted) {
      showStatus("Browser host permission for LinkVault was not granted.", "error");
      return;
    }
    await storageSet({
      linkvaultUrl,
      apiToken: data.apiToken.trim()
    });
    const health = await testLinkVaultConnection();
    await linkvaultRequest("/api/bookmarks");
    showStatus(`Connected. LinkVault ${health.version || ""}`.trim(), "ok");
  } catch (error) {
    showStatus(error.message, "error");
  }
});

loadOptions();

function subnetPrefixFromUrl(value) {
  try {
    const parsed = new URL(value || "");
    const match = parsed.hostname.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.\d{1,3}$/);
    if (!match) return "";
    return `${match[1]}.${match[2]}.${match[3]}`;
  } catch (error) {
    return "";
  }
}

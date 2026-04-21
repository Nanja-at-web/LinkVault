const optionsForm = document.querySelector("#options-form");
const statusEl = document.querySelector("#status");

async function loadOptions() {
  const settings = await getSettings();
  optionsForm.elements.linkvaultUrl.value = settings.linkvaultUrl;
  optionsForm.elements.apiToken.value = settings.apiToken;
}

function showStatus(message, kind = "info") {
  statusEl.textContent = message;
  statusEl.className = `status ${kind}`;
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

document.querySelector("#test-connection").addEventListener("click", async () => {
  try {
    const data = Object.fromEntries(new FormData(optionsForm));
    await storageSet({
      linkvaultUrl: normalizeBaseUrl(data.linkvaultUrl),
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

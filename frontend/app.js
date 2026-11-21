// Global State
let universe = { sectors: {}, groups: {}, supported_tickers: [] };
let activeMetrics = null;
let sectorChartInstance = null;
let stressChartInstance = null;

// Presets
const PRESETS = {
  tech: { NVDA: 30, AAPL: 25, MSFT: 25, GOOGL: 20 },
  ai: { NVDA: 40, AMD: 25, TSM: 20, ASML: 15 },
  balanced: { NVDA: 20, AAPL: 20, MSFT: 20, "BTC-USD": 10, "ETH-USD": 10, AMZN: 20 },
  concentrated: { NVDA: 70, AMD: 20, MSFT: 10 },
};

function getApiBaseUrl() {
  const custom = document.getElementById("api-base-url").value.trim();
  return custom.replace(/\/+$/, "") || "https://auren-api-8yrq.onrender.com";
}

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
  await checkBackendHealth();
  await loadUniverse();
  // Start with 1 empty row ready for user input
  addAssetRow("", "");
  updateTotalWeight();
});

// Backend Health Check
async function checkBackendHealth() {
  const dot = document.getElementById("api-status-dot");
  const text = document.getElementById("api-status-text");
  dot.className = "dot checking";
  text.innerText = "Checking Render API...";

  try {
    const res = await fetch(`${getApiBaseUrl()}/healthz`, { method: "GET" });
    if (res.ok) {
      dot.className = "dot online";
      text.innerText = "Render Backend Online";
    } else {
      dot.className = "dot offline";
      text.innerText = `API HTTP ${res.status}`;
    }
  } catch (err) {
    dot.className = "dot offline";
    text.innerText = "Backend Offline / Waking up";
  }
}

// Load Supported Universe
async function loadUniverse() {
  try {
    const res = await fetch(`${getApiBaseUrl()}/universe`);
    if (res.ok) {
      universe = await res.json();
    }
  } catch (err) {
    console.error("Failed to load universe from API, using fallback list", err);
    universe.supported_tickers = [
      "NVDA", "MSFT", "AAPL", "GOOGL", "AMZN", "META", "AVGO", "ORCL", "NFLX",
      "AMD", "INTC", "QCOM", "MU", "ARM", "TSM", "ASML", "AMAT", "PLTR",
      "TSLA", "BTC-USD", "ETH-USD", "SOL-USD"
    ];
  }
}

// Tab Switching
function switchSidebarTab(tab) {
  document.getElementById("tab-custom").classList.toggle("active", tab === "custom");
  document.getElementById("tab-wallet").classList.toggle("active", tab === "wallet");
  document.getElementById("panel-custom").classList.toggle("active", tab === "custom");
  document.getElementById("panel-wallet").classList.toggle("active", tab === "wallet");
}

// Presets
function applyPreset(name) {
  const p = PRESETS[name];
  if (!p) return;
  const container = document.getElementById("assets-inputs");
  container.innerHTML = "";
  for (const [ticker, weight] of Object.entries(p)) {
    addAssetRow(ticker, weight);
  }
  updateTotalWeight();
}

// Asset Row Management
function addAssetRow(selectedTicker = "", weight = "") {
  const container = document.getElementById("assets-inputs");
  const row = document.createElement("div");
  row.className = "asset-row";

  // Select
  const select = document.createElement("select");
  select.className = "asset-select";
  
  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.text = "-- Select Ticker --";
  select.appendChild(defaultOption);

  const tickers = universe.supported_tickers.length > 0 ? universe.supported_tickers : Object.keys(PRESETS.tech);
  tickers.forEach((t) => {
    const opt = document.createElement("option");
    opt.value = t;
    opt.text = t;
    if (t === selectedTicker) opt.selected = true;
    select.appendChild(opt);
  });

  select.addEventListener("change", () => updateTotalWeight());

  // Weight input
  const input = document.createElement("input");
  input.type = "number";
  input.className = "weight-input";
  input.value = weight;
  input.placeholder = "%";
  input.min = "1";
  input.max = "100";
  input.step = "1";
  input.addEventListener("input", () => updateTotalWeight());

  // Remove button
  const btnRemove = document.createElement("button");
  btnRemove.className = "btn-remove";
  btnRemove.innerHTML = "&times;";
  btnRemove.title = "Remove asset";
  btnRemove.addEventListener("click", () => {
    row.remove();
    updateTotalWeight();
  });

  row.appendChild(select);
  row.appendChild(input);
  row.appendChild(btnRemove);
  container.appendChild(row);
  updateTotalWeight();
}

function updateTotalWeight() {
  const rows = document.querySelectorAll(".asset-row");
  let sum = 0;
  rows.forEach((r) => {
    const val = parseFloat(r.querySelector(".weight-input").value) || 0;
    sum += val;
  });
  const display = document.getElementById("total-weight-display");
  display.innerText = `${Math.round(sum)}%`;
  display.style.color = Math.round(sum) === 100 ? "var(--success)" : "var(--warn)";
}

function getPortfolioWeights() {
  const rows = document.querySelectorAll(".asset-row");
  const weights = {};
  rows.forEach((r) => {
    const t = r.querySelector(".asset-select").value;
    const w = parseFloat(r.querySelector(".weight-input").value) || 0;
    if (t && w > 0) {
      weights[t] = w;
    }
  });
  return weights;
}

// Wallet Inspection
async function importWallet() {
  const addr = document.getElementById("wallet-address").value.trim();
  const infoBox = document.getElementById("wallet-info");
  if (!addr) {
    showAlert("Please enter an EVM/Base address");
    return;
  }

  showAlert(null);
  infoBox.classList.remove("hidden");
  infoBox.innerHTML = "<p class='muted'>Scanning on-chain Base balances...</p>";

  try {
    const res = await fetch(`${getApiBaseUrl()}/wallet`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address: addr }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Wallet lookup failed");
    }

    if (data.portfolio && Object.keys(data.portfolio).length > 0) {
      const container = document.getElementById("assets-inputs");
      container.innerHTML = "";
      for (const [t, w] of Object.entries(data.portfolio)) {
        addAssetRow(t, Math.round(w * 100));
      }
      switchSidebarTab("custom");
      infoBox.innerHTML = `<p class='success-text'>Loaded ${data.holdings_count} tokenized asset(s) into portfolio.</p>`;
      runAnalysis();
    } else {
      infoBox.innerHTML = `<p class='muted'>No tokenized stocks found for ${addr.slice(0, 8)}... (${data.holdings_count} total assets).</p>`;
    }
  } catch (err) {
    infoBox.innerHTML = `<p class='danger-text'>Error: ${err.message}</p>`;
  }
}

// Main Analysis Execution
async function runAnalysis() {
  showAlert(null);
  const weights = getPortfolioWeights();
  if (Object.keys(weights).length === 0) {
    showAlert("Please add at least one asset with positive weight.");
    return;
  }

  const pVal = parseFloat(document.getElementById("portfolio-value").value) || 100000;
  const btn = document.getElementById("btn-analyze");
  const spinner = document.getElementById("loading-spinner");
  btn.disabled = true;
  spinner.classList.remove("hidden");

  try {
    // 1. Fetch Risk Metrics
    const riskRes = await fetch(`${getApiBaseUrl()}/risk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ weights, period: "2y" }),
    });

    const riskData = await riskRes.json();
    if (!riskRes.ok) throw new Error(riskData.detail || "Failed to calculate risk");
    activeMetrics = riskData;

    // Render Metrics
    renderRiskCards(riskData);
    renderReasons(riskData.reasons);
    renderSectorChart(riskData.sector_exposure);
    renderStressChart(riskData.stress);
    renderCorrelationTable(riskData.correlated_pairs);

    // 2. Fetch Liquidity Metrics
    const liqRes = await fetch(`${getApiBaseUrl()}/liquidity`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        portfolio_value: pVal,
        weights,
        adv_participation: 0.1,
      }),
    });

    if (liqRes.ok) {
      const liqData = await liqRes.json();
      renderLiquidityTable(liqData.assets);
    }
  } catch (err) {
    showAlert(err.message);
  } finally {
    btn.disabled = false;
    spinner.classList.add("hidden");
  }
}

// UI Render Helpers
function renderRiskCards(data) {
  // Score
  const scoreEl = document.getElementById("val-score");
  scoreEl.innerText = `${data.score}/100`;

  const badge = document.getElementById("badge-risk-level");
  badge.innerText = data.level.toUpperCase();
  badge.className = `badge ${data.level.toLowerCase()}`;

  // Volatility
  document.getElementById("val-volatility").innerText = `${(data.volatility * 100).toFixed(1)}%`;

  // Drawdown
  document.getElementById("val-drawdown").innerText = `${(data.max_drawdown * 100).toFixed(1)}%`;

  // Effective Assets
  document.getElementById("val-effective-assets").innerText = data.concentration.effective_assets.toFixed(1);
  document.getElementById("sub-concentration").innerText = `HHI: ${data.concentration.hhi.toFixed(3)} | Top: ${data.concentration.top_asset} (${(data.concentration.top_weight * 100).toFixed(0)}%)`;
}

function renderReasons(reasons) {
  const container = document.getElementById("risk-reasons-list");
  if (!reasons || reasons.length === 0) {
    container.innerHTML = '<div class="callout muted">No major risk flags detected. Well-balanced portfolio.</div>';
    return;
  }
  container.innerHTML = reasons
    .map((r) => `<div class="callout flag">⚠️ <strong>${r}</strong></div>`)
    .join("");
}

function renderSectorChart(sectors) {
  const ctx = document.getElementById("sectorChart").getContext("2d");
  if (sectorChartInstance) sectorChartInstance.destroy();

  const labels = Object.keys(sectors);
  const rawShares = Object.values(sectors);
  const data = rawShares.map((v) => v * 100);

  sectorChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data,
          rawShares,
          backgroundColor: [
            "#E3B341", "#8A8F98", "#F87171", "#4ADE80",
            "#FBBF24", "#60A5FA", "#A78BFA", "#F472B6"
          ],
          borderColor: "#18181B",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: { color: "#8A8F98", font: { family: "Inter", size: 11 } },
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || "";
              const rawShare = (context.dataset && context.dataset.rawShares && context.dataset.rawShares[context.dataIndex] !== undefined)
                ? context.dataset.rawShares[context.dataIndex]
                : (sectors && sectors[label] !== undefined ? sectors[label] : ((context.parsed || 0) / 100));
              const pct = Math.round(rawShare * 100);
              const pValInput = (typeof document !== "undefined" && document.getElementById)
                ? document.getElementById("portfolio-value")
                : null;
              const pVal = pValInput ? (parseFloat(pValInput.value) || 0) : 0;
              const dollarVal = Math.round(rawShare * pVal);
              return ` ${label}: ${pct}% ($${dollarVal.toLocaleString()})`;
            },
          },
        },
      },
    },
  });
}

function renderStressChart(stress) {
  const ctx = document.getElementById("stressChart").getContext("2d");
  if (stressChartInstance) stressChartInstance.destroy();

  const labels = Object.keys(stress);
  const data = Object.values(stress).map((v) => (v * 100).toFixed(1));
  const bgColors = data.map((v) => (v >= 0 ? "rgba(74, 222, 128, 0.7)" : "rgba(248, 113, 113, 0.7)"));

  stressChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Portfolio Impact (%)",
          data,
          backgroundColor: bgColors,
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          ticks: { color: "#8A8F98", font: { size: 10 } },
          grid: { display: false },
        },
        y: {
          ticks: {
            color: "#8A8F98",
            callback: (v) => `${v}%`,
          },
          grid: { color: "#26262B" },
        },
      },
    },
  });
}

function renderCorrelationTable(pairs) {
  const container = document.getElementById("correlation-table-container");
  if (!pairs || pairs.length === 0) {
    container.innerHTML = '<p class="placeholder-text">No pairs exceed the 0.70 correlation threshold.</p>';
    return;
  }

  let html = `<table class="table-custom">
    <thead>
      <tr><th>Asset A</th><th>Asset B</th><th style="text-align:right;">Correlation (ρ)</th></tr>
    </thead>
    <tbody>`;

  pairs.forEach(([a, b, corr]) => {
    html += `<tr>
      <td class="mono">${a}</td>
      <td class="mono">${b}</td>
      <td class="mono" style="text-align:right; color: var(--danger);">${corr.toFixed(2)}</td>
    </tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}

function renderLiquidityTable(assets) {
  const container = document.getElementById("liquidity-table-container");
  if (!assets || assets.length === 0) {
    container.innerHTML = '<p class="placeholder-text">Liquidity data unavailable.</p>';
    return;
  }

  let html = `<table class="table-custom">
    <thead>
      <tr><th>Asset</th><th>Value</th><th>30D ADV</th><th style="text-align:right;">Days to Exit</th></tr>
    </thead>
    <tbody>`;

  assets.forEach((item) => {
    const daysColor = item.days_to_exit > 3 ? "var(--danger)" : item.days_to_exit > 1 ? "var(--warn)" : "var(--text-main)";
    html += `<tr>
      <td class="mono">${item.ticker}</td>
      <td class="mono">$${item.holding_value.toLocaleString()}</td>
      <td class="mono">$${Math.round(item.adv).toLocaleString()}</td>
      <td class="mono" style="text-align:right; color: ${daysColor};">${item.days_to_exit.toFixed(1)}d</td>
    </tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}

// Generate AI Report
async function generateAiReport() {
  if (!activeMetrics) {
    showAlert("Please run risk analysis first.");
    return;
  }

  const btn = document.getElementById("btn-ai-report");
  const spinner = document.getElementById("ai-spinner");
  const btnText = document.getElementById("ai-btn-text");
  const reportBox = document.getElementById("ai-report-body");

  btn.disabled = true;
  spinner.classList.remove("hidden");
  btnText.innerText = "Generating...";
  reportBox.innerHTML = "<p class='muted'>Contacting LLM risk analyst on Render...</p>";

  try {
    const res = await fetch(`${getApiBaseUrl()}/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ metrics: activeMetrics }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to generate AI report");

    let text = data.report;
    if (data.unverified_numbers && data.unverified_numbers.length > 0) {
      text += `\n\n[Engine Audit Note: Unverified numbers flagged: ${data.unverified_numbers.join(", ")}]`;
    }

    reportBox.innerText = text;
  } catch (err) {
    reportBox.innerHTML = `<p class="danger-text">Report generation failed: ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    spinner.classList.add("hidden");
    btnText.innerText = "Generate AI Report";
  }
}

function showAlert(msg) {
  const el = document.getElementById("alert-banner");
  if (!msg) {
    el.classList.add("hidden");
    el.innerText = "";
  } else {
    el.classList.remove("hidden");
    el.className = "alert error";
    el.innerText = msg;
  }
}

"use strict";
/* AUREN risk intelligence client
   Nine analysis tabs, presets, what-if comparison, custom stress shocks,
   liquidity, and a hallucination-checked AI report. */

// ------------------------------------------------------------------ Constants
const C = { gold: "#D6B25E", muted: "#8E9199", line: "#232329", text: "#EDEBE6", danger: "#E5786F", ok: "#6FCF97", warn: "#E0A458", bg: "#0A0A0C" };
const GREYS = ["#5B5F68", "#7A7F88", "#A3A7AF", "#C9CCD2", "#E1E3E6", "#44474F"];
const DEFAULT_API = "https://auren-api-8yrq.onrender.com";

const PRESETS = {
  "Balanced Tech & Crypto (Default)": [["NVDA", 40], ["MSFT", 30], ["GOOGL", 20], ["ETH-USD", 10]],
  "Magnificent 7 Tech Heavy": [["NVDA", 25], ["MSFT", 20], ["AAPL", 20], ["AMZN", 15], ["GOOGL", 10], ["META", 10]],
  "Diversified All-Weather": [["MSFT", 20], ["JPM", 20], ["COST", 20], ["GLD", 20], ["BTC-USD", 10], ["ETH-USD", 10]],
  "High Conviction Semiconductor": [["NVDA", 50], ["TSM", 25], ["ASML", 15], ["AMD", 10]],
};
const DEFAULT_PRESET = "Balanced Tech & Crypto (Default)";

const DEFAULT_SECTORS = {
  NVDA: "Semiconductors", MSFT: "Software", AAPL: "Consumer Technology", GOOGL: "Internet & AI", AMZN: "E-Commerce & Cloud",
  META: "Social Media", AVGO: "Semiconductors", ORCL: "Software & Cloud", NFLX: "Entertainment", AMD: "Semiconductors",
  INTC: "Semiconductors", QCOM: "Semiconductors", MU: "Memory Chips", ARM: "Semiconductors", TSM: "Semiconductors",
  ASML: "Semiconductor Equipment", PLTR: "AI & Data Analytics", TSLA: "Automotive", COST: "Retail", WMT: "Retail",
  JPM: "Financials", GLD: "Gold", "BTC-USD": "Crypto", "ETH-USD": "Crypto", "SOL-USD": "Crypto",
};
const DEFAULT_GROUPS = {
  NVDA: "AI & Semiconductors", MSFT: "Big Tech", AAPL: "Big Tech", GOOGL: "Big Tech", AMZN: "Big Tech", META: "Big Tech",
  AVGO: "AI & Semiconductors", ORCL: "Big Tech", NFLX: "Big Tech", AMD: "AI & Semiconductors", INTC: "AI & Semiconductors",
  QCOM: "AI & Semiconductors", MU: "AI & Semiconductors", ARM: "AI & Semiconductors", TSM: "AI & Semiconductors",
  ASML: "AI & Semiconductors", PLTR: "Software & Cybersecurity", TSLA: "Consumer & Retail", COST: "Consumer & Retail",
  WMT: "Consumer & Retail", JPM: "Financials", GLD: "Gold", "BTC-USD": "Crypto", "ETH-USD": "Crypto", "SOL-USD": "Crypto",
};

// ------------------------------------------------------------------ State
let universe = { sectors: DEFAULT_SECTORS, groups: DEFAULT_GROUPS, supported_tickers: Object.keys(DEFAULT_SECTORS).sort() };
let analysis = null, liquidity = null, whatIf = null, lastReport = "", busy = false;
const customShocks = {};
const charts = {};

// ------------------------------------------------------------------ Helpers
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pct = (v, d = 1) => `${(v * 100).toFixed(d)}%`;
const usd = (v) => `${v < 0 ? "−" : ""}$${Math.round(Math.abs(v)).toLocaleString()}`;
const signed = (v, d = 1) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v * 100).toFixed(d)}%`;
const levelClass = (l) => ({ Low: "ok", Medium: "warn", High: "danger" }[l] || "muted");
const badge = (l) => `<span class="badge ${levelClass(l)}">${esc(l)} risk</span>`;
const base = () => {
  const input = $("api-base-url");
  const val = input ? input.value.trim().replace(/\/+$/, "") : "";
  return val || localStorage.getItem("auren_api_url") || DEFAULT_API;
};
const getSize = () => Math.max(100, parseFloat($("portfolio-value").value) || 10000);
const sum = (o) => Object.values(o).reduce((a, b) => a + b, 0);

function errText(d) {
  if (!d || d.detail == null) return "";
  return Array.isArray(d.detail) ? d.detail.map((x) => x.msg || JSON.stringify(x)).join("; ") : String(d.detail);
}

async function api(path, { method = "GET", body, timeout = 60000 } = {}) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), timeout);
  try {
    const res = await fetch(base() + path, {
      method, signal: ctl.signal,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    let data = null;
    try { data = await res.json(); } catch { /* non-JSON response */ }
    if (!res.ok) throw new Error(errText(data) || `The server returned an error (${res.status}).`);
    return data;
  } catch (e) {
    if (e.name === "AbortError") throw new Error("The server took too long to respond. It may be waking up, so try again in a moment.");
    if (e instanceof TypeError) throw new Error("Can't reach the server. Check your connection or the backend URL in Server settings.");
    throw e;
  } finally { clearTimeout(timer); }
}

function showAlert(msg) {
  const el = $("alert-banner");
  if (!msg) { el.hidden = true; el.innerHTML = ""; return; }
  el.innerHTML = `<span>${esc(msg)}</span><button type="button" aria-label="Dismiss">×</button>`;
  el.querySelector("button").onclick = () => showAlert(null);
  el.hidden = false;
}

function setBusy(btn, on, label) {
  btn.disabled = on;
  btn.querySelector(".spinner").hidden = !on;
  if (label) btn.querySelector(".btn-label").textContent = label;
}

// ------------------------------------------------------------------ Lifecycle
document.addEventListener("DOMContentLoaded", async () => {
  Chart.defaults.color = C.muted;
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  Chart.defaults.borderColor = C.line;
  Object.assign(Chart.defaults.plugins.tooltip, { backgroundColor: "#17171B", borderColor: "#2E2E36", borderWidth: 1, titleColor: C.text, bodyColor: C.muted, padding: 10, cornerRadius: 8, displayColors: true, boxPadding: 4 });
  Chart.register({
    id: "threshold",
    afterDatasetsDraw(chart, _a, o) {
      if (o.value == null) return;
      const { ctx, chartArea: { top, bottom }, scales: { x } } = chart;
      const px = x.getPixelForValue(o.value);
      ctx.save();
      ctx.strokeStyle = C.danger; ctx.setLineDash([5, 4]); ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(px, top); ctx.lineTo(px, bottom); ctx.stroke();
      ctx.setLineDash([]); ctx.fillStyle = C.danger; ctx.font = "12px Inter"; ctx.textAlign = "right";
      ctx.fillText(o.label, px - 6, top + 12);
      ctx.restore();
    },
  });

  const savedUrl = localStorage.getItem("auren_api_url");
  if (savedUrl && $("api-base-url")) {
    $("api-base-url").value = savedUrl;
  }
  if ($("api-base-url")) {
    $("api-base-url").addEventListener("change", (e) => {
      const v = e.target.value.trim().replace(/\/+$/, "");
      if (v) localStorage.setItem("auren_api_url", v);
    });
  }

  bindEvents();
  loadPreset(DEFAULT_PRESET);
  cloneToWhatIf();
  setLoading(true);
  await checkHealth();
  if (await loadUniverse()) { loadPreset(DEFAULT_PRESET); cloneToWhatIf(); }
  await runAnalysis();
});

function bindEvents() {
  setupTabs();
  $("preset-select").onchange = (e) => { if (PRESETS[e.target.value]) { loadPreset(e.target.value); runAnalysis(); } };
  $("btn-add").onclick = () => { addRow("assets-inputs", "", "", onHoldingsEdit); $("assets-inputs").lastElementChild.querySelector("select").focus(); };
  $("btn-normalize").onclick = () => normalize("assets-inputs", updateTotal);
  $("btn-analyze").onclick = runAnalysis;
  $("portfolio-value").onchange = () => analysis && runAnalysis();
  $("btn-wallet").onclick = importWallet;
  $("wallet-address").onkeydown = (e) => { if (e.key === "Enter") importWallet(); };
  $("btn-health").onclick = async () => { const up = await checkHealth(); showAlert(up ? null : "Can't reach the server. Check the backend URL and try again."); if (!up) return; if (await loadUniverse()) loadPreset($("preset-select").value in PRESETS ? $("preset-select").value : DEFAULT_PRESET); };
  $("wf-add").onclick = () => addRow("wf-inputs", "", "", updateWhatIfTotal);
  $("wf-reset").onclick = cloneToWhatIf;
  $("wf-norm").onclick = () => normalize("wf-inputs", updateWhatIfTotal);
  $("wf-run").onclick = runWhatIf;
  $("btn-ai").onclick = generateReport;
  $("btn-dl").onclick = downloadReport;
}

// ------------------------------------------------------------------ Tabs (keyboard accessible)
function setupTabs() {
  const tabs = [...document.querySelectorAll(".tab")];
  const select = (tab, focus) => {
    tabs.forEach((t) => {
      const on = t === tab;
      t.classList.toggle("active", on);
      t.setAttribute("aria-selected", on);
      t.tabIndex = on ? 0 : -1;
      const p = $(t.getAttribute("aria-controls"));
      p.hidden = !on; p.classList.toggle("active", on);
    });
    if (focus) tab.focus();
    tab.scrollIntoView({ block: "nearest", inline: "center" });
    Object.values(charts).forEach((c) => c.resize());
  };
  tabs.forEach((t, i) => {
    t.onclick = () => select(t);
    t.onkeydown = (e) => {
      const k = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
      if (k) { e.preventDefault(); select(tabs[(i + k + tabs.length) % tabs.length], true); }
      if (e.key === "Home") { e.preventDefault(); select(tabs[0], true); }
      if (e.key === "End") { e.preventDefault(); select(tabs[tabs.length - 1], true); }
    };
  });
}

// ------------------------------------------------------------------ Backend
async function checkHealth() {
  for (let n = 1; n <= 4; n++) {
    try { await api("/healthz", { timeout: 20000 }); return true; } catch { /* retry while the server wakes up */ }
  }
  return false;
}

async function loadUniverse() {
  try {
    const d = await api("/universe", { timeout: 15000 });
    if (d && d.supported_tickers && d.supported_tickers.length) { universe = d; return true; }
  } catch { console.warn("Using built-in ticker list"); }
  return false;
}

// ------------------------------------------------------------------ Holdings editor
function tickerOptions(selected) {
  const groups = {};
  universe.supported_tickers.forEach((t) => (groups[universe.groups[t] || "Other"] ||= []).push(t));
  return `<option value="">Select a ticker</option>` + Object.keys(groups).sort().map((g) =>
    `<optgroup label="${esc(g)}">${groups[g].map((t) => `<option value="${esc(t)}"${t === selected ? " selected" : ""}>${esc(t)}</option>`).join("")}</optgroup>`).join("");
}

function addRow(containerId, ticker, weight, onChange) {
  const row = document.createElement("div");
  row.className = "asset-row";
  row.innerHTML = `<select class="field asset-select" aria-label="Ticker">${tickerOptions(ticker)}</select>
    <div class="weight"><input class="field weight-input" type="number" min="0" max="100" step="1" inputmode="decimal" placeholder="0" aria-label="Weight in percent"><span>%</span></div>
    <button class="icon-btn" type="button" aria-label="Remove holding">×</button>`;
  row.querySelector(".weight-input").value = weight;
  row.querySelector("select").onchange = onChange;
  row.querySelector("input").oninput = onChange;
  row.querySelector("button").onclick = () => { row.remove(); onChange(); };
  $(containerId).appendChild(row);
  onChange();
}

const onHoldingsEdit = () => { $("preset-select").value = "Custom / Edited"; updateTotal(); };

function readWeights(containerId) {
  const w = {};
  $(containerId).querySelectorAll(".asset-row").forEach((r) => {
    const t = r.querySelector("select").value.trim().toUpperCase();
    const v = parseFloat(r.querySelector("input").value) || 0;
    if (t && v > 0) w[t] = (w[t] || 0) + v;
  });
  return w;
}

function setTotal(chipId, normId, label) {
  const total = sum(readWeights(chipId === "total-chip" ? "assets-inputs" : "wf-inputs"));
  const ok = Math.abs(total - 100) <= 0.05;
  const chip = $(chipId);
  chip.textContent = `${label} ${total.toFixed(1)}%`;
  chip.className = `chip ${ok ? "ok" : "bad"}`;
  $(normId).hidden = ok;
}
const updateTotal = () => setTotal("total-chip", "btn-normalize", "Total");
const updateWhatIfTotal = () => setTotal("wf-chip", "wf-norm", "Total");

function normalize(containerId, after) {
  const rows = [...$(containerId).querySelectorAll(".asset-row")];
  const total = rows.reduce((a, r) => a + (parseFloat(r.querySelector("input").value) || 0), 0);
  if (total <= 0) return;
  rows.forEach((r) => { const i = r.querySelector("input"); i.value = (((parseFloat(i.value) || 0) / total) * 100).toFixed(1); });
  after();
}

function loadPreset(name) {
  $("assets-inputs").innerHTML = "";
  (PRESETS[name] || []).forEach(([t, w]) => addRow("assets-inputs", t, w, onHoldingsEdit));
  $("preset-select").value = name;
  updateTotal();
}

// ------------------------------------------------------------------ Wallet import
function walletMsg(type, text) { const el = $("wallet-msg"); el.hidden = false; el.className = `note ${type}`; el.textContent = text; }

async function importWallet() {
  const address = $("wallet-address").value.trim();
  if (!/^0x[a-fA-F0-9]{40}$/.test(address)) return walletMsg("error", "Enter a Base address: 0x followed by 40 hex characters.");
  walletMsg("warning", "Scanning tokenized balances on Base…");
  try {
    const d = await api("/wallet", { method: "POST", body: { address } });
    const entries = Object.entries(d.portfolio || {});
    if (!entries.length) return walletMsg("warning", "No supported tokenized stocks found in this wallet.");
    $("assets-inputs").innerHTML = "";
    entries.forEach(([t, w]) => addRow("assets-inputs", t, (w * 100).toFixed(1), onHoldingsEdit));
    $("preset-select").value = "Custom / Edited";
    renderWalletTable(d.holdings || []);
    walletMsg("success", `Loaded ${entries.length} tokenized stock${entries.length > 1 ? "s" : ""}.`);
    runAnalysis();
  } catch (e) { walletMsg("error", `Couldn't read the wallet: ${e.message}`); }
}

function renderWalletTable(rows) {
  $("wallet-box").hidden = !rows.length;
  $("wallet-body").innerHTML = rows.map((r) => `<tr>
    <td>${esc(r.token ?? "–")}</td><td><strong>${esc(r.ticker ?? "–")}</strong></td>
    <td class="num">${esc(r.tokens ?? "–")}</td><td class="num">${esc(r.shares ?? "–")}</td>
    <td class="num">${r.price ? "$" + Number(r.price).toFixed(2) : "–"}</td>
    <td class="num">${r.value ? "$" + Number(r.value).toLocaleString() : "–"}</td>
    <td>${r.supported ? '<span class="chip ok">Yes</span>' : '<span class="chip bad">No</span>'}</td></tr>`).join("");
}

// ------------------------------------------------------------------ Analysis
function setLoading(on) {
  $("workspace").classList.toggle("is-loading", on);
  $("workspace").setAttribute("aria-busy", on);
  $("loadbar").hidden = !on;
}

async function runAnalysis() {
  if (busy) return;
  showAlert(null);
  const weights = readWeights("assets-inputs");
  if (!Object.keys(weights).length) return showAlert("Add at least one holding to start.");
  const total = sum(weights);
  if (Math.abs(total - 100) > 0.1) return showAlert(`Your weights add up to ${total.toFixed(1)}%. They need to total 100%. Use “Scale to 100%” to fix it.`);

  busy = true; setLoading(true); setBusy($("btn-analyze"), true, "Analysing…");
  const size = getSize();
  try {
    analysis = await api("/risk", { method: "POST", body: { weights, period: "2y" } });
    try { liquidity = await api("/liquidity", { method: "POST", body: { portfolio_value: size, weights, adv_participation: 0.1 } }); }
    catch { liquidity = null; }
    renderAll(size, weights);
  } catch (e) { showAlert(e.message); }
  finally { busy = false; setLoading(false); setBusy($("btn-analyze"), false, "Run risk analysis"); }
}

function safe(fn, ...a) { try { fn(...a); } catch (e) { console.error(fn.name, e); } }

function renderAll(size, weights) {
  const A = analysis;
  safe(renderSidebarScore, A); safe(renderPortfolio, A, size, weights); safe(renderConcentration, A, size);
  safe(renderScore, A); safe(renderHistory, A); safe(renderStress, A, size, weights);
  safe(renderLiquidity, liquidity); safe(renderCorrelation, A); safe(renderInspector, A, size);
}

function chart(id, config) {
  charts[id]?.destroy();
  charts[id] = new Chart($(id).getContext("2d"), config);
}

// ------------------------------------------------------------------ Sidebar + score
function renderSidebarScore(A) {
  $("sb-score").textContent = A.score;
  $("sb-level").className = `badge ${levelClass(A.level)}`;
  $("sb-level").textContent = `${A.level} risk`;
  const bar = $("sb-bar");
  bar.style.width = `${Math.min(100, Math.max(0, A.score))}%`;
  bar.style.background = `var(--${{ ok: "ok", warn: "warn", danger: "danger", muted: "gold" }[levelClass(A.level)]})`;
}

function renderScore(A) {
  const lc = levelClass(A.level);
  $("gauge-fill").setAttribute("class", `gauge-fill ${lc}`);
  $("gauge-fill").style.strokeDasharray = `${Math.min(100, Math.max(0, A.score))} 100`;
  $("gauge-val").textContent = A.score;
  $("gauge-level").className = `badge ${lc}`;
  $("gauge-level").textContent = `${A.level} risk`;
  const box = $("hits");
  box.innerHTML = !A.hits || !A.hits.length
    ? '<div class="callout good">No risk rules were triggered for this portfolio.</div>'
    : A.hits.map(([pts, why]) => `<div class="callout"><strong>+${esc(pts)} points</strong> &nbsp;${esc(why)}</div>`).join("");
}

// ------------------------------------------------------------------ Portfolio tab
function renderPortfolio(A, size, raw) {
  const c = A.concentration;
  $("kpi-value").textContent = usd(size);
  $("kpi-top").textContent = `${c.top_asset} ${pct(c.top_weight, 0)}`;
  $("kpi-eff").textContent = c.effective_assets.toFixed(1);
  $("kpi-eff-sub").textContent = `Acts like ${c.effective_assets.toFixed(1)} equal holdings, not ${Object.keys(raw).length}`;
  const top = Object.entries(A.sector_exposure || {}).sort((a, b) => b[1] - a[1])[0];
  $("kpi-sector").textContent = top ? pct(top[1], 0) : "–";
  $("kpi-sector-sub").textContent = top ? top[0] : "–";

  $("holdings-body").innerHTML = Object.entries(A.normalized_weights).map(([t, w]) => `<tr>
    <td><strong>${esc(t)}</strong></td><td class="cell-muted">${esc(universe.sectors[t] || "Unknown")}</td>
    <td class="cell-muted">${esc(universe.groups[t] || "Other")}</td>
    <td class="num"><span class="wbar"><i style="width:${Math.min(100, w * 100)}%"></i></span>${pct(w)}</td>
    <td class="num">${usd(w * size)}</td></tr>`).join("");

  const labels = Object.keys(A.normalized_weights);
  chart("allocationChart", {
    type: "doughnut",
    data: { labels, datasets: [{ data: labels.map((t) => +(A.normalized_weights[t] * 100).toFixed(1)), backgroundColor: labels.map((t, i) => t === c.top_asset ? C.gold : GREYS[i % GREYS.length]), borderColor: C.bg, borderWidth: 2 }] },
    options: { responsive: true, maintainAspectRatio: false, cutout: "62%", plugins: { legend: { position: "right", labels: { usePointStyle: true, boxWidth: 8 } },
      tooltip: { callbacks: { label: (x) => `${x.label}: ${x.raw}% (${usd((x.raw / 100) * size)})` } } } },
  });

  const sorted = Object.entries(A.sector_exposure || {}).sort((a, b) => a[1] - b[1]);
  const vals = sorted.map((s) => +(s[1] * 100).toFixed(1)), max = Math.max(0, ...vals);
  chart("sectorChart", barConfig(sorted.map((s) => s[0]), vals, (v) => v === max, 50, "50% rule", Math.max(55, max * 1.15)));
}

function barConfig(labels, data, highlight, threshold, thresholdLabel, suggestedMax) {
  return {
    type: "bar",
    data: { labels, datasets: [{ data, backgroundColor: data.map((v) => (highlight(v) ? C.gold : "#5B5F68")), borderRadius: 5, maxBarThickness: 28 }] },
    options: {
      indexAxis: "y", responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, threshold: { value: threshold, label: thresholdLabel }, tooltip: { callbacks: { label: (x) => `${x.raw}%` } } },
      scales: { x: { min: 0, suggestedMax, ticks: { callback: (v) => `${v}%` }, grid: { color: C.line } }, y: { ticks: { color: C.text }, grid: { display: false } } },
    },
  };
}

// ------------------------------------------------------------------ Concentration tab
function renderConcentration(A, size) {
  const c = A.concentration;
  $("c-top").textContent = `${c.top_asset} ${pct(c.top_weight, 0)}`;
  $("c-top3").textContent = pct(c.top3_weight, 0);
  $("c-eff").textContent = c.effective_assets.toFixed(1);
  $("c-hhi").textContent = c.hhi.toFixed(2);

  const sorted = Object.entries(A.normalized_weights).sort((a, b) => a[1] - b[1]);
  const vals = sorted.map((s) => +(s[1] * 100).toFixed(1));
  chart("concChart", barConfig(sorted.map((s) => s[0]), vals, (v) => v > 30, 30, "30% rule", Math.max(35, Math.max(...vals) * 1.2)));

  const over = c.top_weight > 0.3;
  $("c-warn").className = `callout ${over ? "danger" : "good"}`;
  $("c-warn").innerHTML = over
    ? `<strong>${esc(c.top_asset)}</strong> makes up ${pct(c.top_weight)} of the portfolio, above the 30% limit. This adds 20 risk points.`
    : `No single holding is above 30%. The largest, <strong>${esc(c.top_asset)}</strong>, is ${pct(c.top_weight)}.`;
  $("c-shock").innerHTML = `If ${esc(c.top_asset)} fell 20%, the portfolio would lose about <strong>${pct(c.top_weight * 0.2)} (${usd(c.top_weight * 0.2 * size)})</strong> from that holding alone. This is simple arithmetic, not a forecast.`;

  const w = Object.values(A.normalized_weights).sort((a, b) => b - a), n = w.length;
  $("c-math").innerHTML = `<p><strong>Concentration index (HHI)</strong></p>
    <p class="gold">HHI = Σ w² = ${w.map((x) => x.toFixed(2) + "²").join(" + ")} = <strong>${c.hhi.toFixed(4)}</strong></p>
    <p><strong>Effective assets</strong></p>
    <p class="gold">1 ÷ HHI = 1 ÷ ${c.hhi.toFixed(4)} = <strong>${c.effective_assets.toFixed(2)}</strong></p>
    <p class="hint">With ${n} equal holdings of ${(100 / n).toFixed(1)}% each, effective assets would be ${n}.</p>`;
}

// ------------------------------------------------------------------ History tab
function thin(arr, step) { return arr.filter((_, i) => i % step === 0); }

function renderHistory(A) {
  const wp = A.worst_historical_periods || {};
  $("h-vol").textContent = pct(A.volatility);
  $("h-mdd").textContent = pct(A.max_drawdown);
  $("h-day").textContent = wp.worst_day != null ? pct(wp.worst_day) : "–";
  $("h-month").textContent = wp.worst_month != null ? pct(wp.worst_month) : "–";

  const dates = A.dates || [], step = Math.max(1, Math.floor(dates.length / 250)), labels = thin(dates, step);
  let i = 0;
  const datasets = Object.entries(A.price_series || {}).map(([name, v]) => {
    const isPf = name === "Portfolio";
    return { label: isPf ? "Portfolio" : name, data: thin(v, step), borderColor: isPf ? C.gold : GREYS[i++ % GREYS.length], borderWidth: isPf ? 2.8 : 1.2, pointRadius: 0, tension: 0.1, order: isPf ? 0 : 1 };
  });
  chart("priceChart", { type: "line", data: { labels, datasets }, options: lineOptions({ legend: true }) });

  chart("ddChart", {
    type: "line",
    // Drawdown keeps the full series: thinning can drop a single-session dip
    // entirely while max_drawdown still reports it (#190). The x-axis already
    // limits displayed ticks, so full resolution costs nothing visible.
    data: { labels: dates, datasets: [{ label: "Drawdown", data: (A.drawdown_series || []).map((v) => v * 100), borderColor: C.gold, backgroundColor: "rgba(214,178,94,0.14)", fill: true, borderWidth: 1.8, pointRadius: 0, tension: 0.1 }] },
    options: lineOptions({ pct: true, min: A.max_drawdown ? A.max_drawdown * 120 : undefined, max: 2 }),
  });
}

function lineOptions({ legend = false, pct: isPct = false, min, max } = {}) {
  return {
    responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
    plugins: { legend: { display: legend, position: "bottom", labels: { usePointStyle: true, boxWidth: 8 } },
      tooltip: { callbacks: { label: (x) => `${x.dataset.label}: ${Number(x.raw).toFixed(isPct ? 1 : 1)}${isPct ? "%" : ""}` } } },
    scales: { x: { ticks: { maxTicksLimit: 8 }, grid: { display: false } }, y: { suggestedMin: min, suggestedMax: max, ticks: { callback: (v) => (isPct ? `${v}%` : v) }, grid: { color: C.line } } },
  };
}

// ------------------------------------------------------------------ Stress tab
function renderStress(A, size, weights) {
  const entries = Object.entries(A.stress || {});
  $("stress-cards").innerHTML = entries.map(([name, imp]) => `<div class="kpi"><span class="kpi-label">${esc(name)}</span>
    <span class="kpi-val ${imp < -0.15 ? "danger" : "gold"}">${signed(imp)}</span><span class="kpi-sub">${imp >= 0 ? "+" : ""}${usd(imp * size)}</span></div>`).join("");
  $("stress-body").innerHTML = entries.map(([name, imp]) => `<tr><td><strong>${esc(name)}</strong></td>
    <td class="num" style="color:${imp < 0 ? C.danger : C.ok}">${signed(imp)}</td>
    <td class="num">${imp >= 0 ? "+" : ""}${usd(imp * size)}</td><td class="num">${usd(size * (1 + imp))}</td></tr>`).join("");

  const box = $("sliders");
  box.innerHTML = "";
  [...new Set(Object.keys(weights).map((t) => universe.groups[t] || "Other"))].sort().forEach((g) => {
    customShocks[g] ??= 0;
    const id = "shock-" + g.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
    const div = document.createElement("div");
    div.innerHTML = `<div class="slider-head"><label for="${id}">${esc(g)}</label><output for="${id}">${customShocks[g]}%</output></div>
      <input id="${id}" type="range" min="-50" max="20" step="5" value="${customShocks[g]}">`;
    div.querySelector("input").oninput = (e) => {
      customShocks[g] = +e.target.value;
      div.querySelector("output").textContent = `${e.target.value}%`;
      applyCustomShock();
    };
    box.appendChild(div);
  });
  applyCustomShock();
}

function applyCustomShock() {
  if (!analysis) return;
  const size = getSize();
  const impact = Object.entries(analysis.normalized_weights).reduce((a, [t, w]) => a + w * ((customShocks[universe.groups[t] || "Other"] || 0) / 100), 0);
  const val = $("custom-val");
  val.textContent = signed(impact);
  val.className = `kpi-val ${impact < 0 ? "danger" : impact > 0 ? "success" : ""}`;
  $("custom-dollar").textContent = `${impact >= 0 ? "+" : ""}${usd(impact * size)} on ${usd(size)}`;
  const note = $("custom-note");
  note.className = `callout ${impact < 0 ? "danger" : impact > 0 ? "good" : "muted"}`;
  note.innerHTML = impact < 0 ? `Under this scenario your portfolio would fall <strong>${pct(-impact)}</strong>, a loss of <strong>${usd(-impact * size)}</strong>.`
    : impact > 0 ? `Under this scenario your portfolio would gain <strong>${pct(impact)}</strong>, or <strong>${usd(impact * size)}</strong>.`
    : "Move a slider to see the effect on your portfolio.";
}

// ------------------------------------------------------------------ Liquidity tab
function renderLiquidity(liq) {
  const body = $("liq-body"), note = $("liq-note");
  if (!liq || !liq.assets) {
    body.innerHTML = ""; $("l-max").textContent = "–"; $("l-ticker").textContent = "–";
    note.className = "callout muted"; note.textContent = "Liquidity data isn't available right now. Run the analysis again to retry.";
    return;
  }
  const worst = liq.assets.reduce((m, a) => (a.days_to_exit > m.days_to_exit ? a : m), liq.assets[0]);
  $("l-max").textContent = `${liq.max_days_to_exit.toFixed(2)} days`;
  $("l-ticker").textContent = `Slowest to sell: ${worst.ticker}`;
  body.innerHTML = liq.assets.map((a) => {
    const d = a.days_to_exit, cls = d >= 1 ? "bad" : d >= 0.1 ? "warn" : "ok", status = d >= 1 ? "Slow (1+ days)" : d >= 0.1 ? "Liquid (under 1 day)" : "Instant (under 0.1 day)";
    return `<tr><td><strong>${esc(a.ticker)}</strong></td><td class="num">${usd(a.holding_value)}</td><td class="num">${usd(a.adv)}</td>
      <td class="num">${usd(a.adv * 0.1)}</td><td class="num"><strong>${d.toFixed(3)}</strong></td><td><span class="chip ${cls}">${status}</span></td></tr>`;
  }).join("");
  const slow = liq.max_days_to_exit > 1;
  note.className = `callout ${slow ? "danger" : "good"}`;
  note.innerHTML = slow
    ? `Selling <strong>${esc(worst.ticker)}</strong> would take ${liq.max_days_to_exit.toFixed(2)} trading days at 10% of daily volume.`
    : "Every position can be sold within one trading day at 10% of daily volume.";
}

// ------------------------------------------------------------------ Correlation tab
function renderCorrelation(A) {
  const m = A.correlation_matrix || { columns: [], data: [] }, pairs = A.correlated_pairs || [], n = m.columns.length;
  let best = null;
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) if (!best || m.data[i][j] > best.v) best = { v: m.data[i][j], a: m.columns[i], b: m.columns[j] };
  $("r-pair").textContent = best ? `${best.a} & ${best.b}` : "–";
  $("r-pair-sub").textContent = best ? `Correlation ${best.v.toFixed(2)}` : "Add at least 2 holdings";
  $("r-count").textContent = pairs.length;
  $("r-total").textContent = `Out of ${(n * (n - 1)) / 2} pairs`;

  $("matrix").innerHTML = !n ? '<p class="muted-text">Run an analysis to see the matrix.</p>'
    : `<table class="table matrix"><thead><tr><th></th>${m.columns.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${m.data.map((row, r) =>
      `<tr><th scope="row">${esc(m.columns[r])}</th>${row.map((v, c) => {
        const self = r === c, hi = !self && v >= 0.7;
        const bg = self ? "rgba(255,255,255,.05)" : `rgba(214,178,94,${Math.max(0, v) * (hi ? 0.5 : 0.22)})`;
        return `<td style="background:${bg};color:${hi ? C.gold : self ? C.muted : C.text};font-weight:${hi ? 700 : 400}">${v.toFixed(2)}</td>`;
      }).join("")}</tr>`).join("")}</tbody></table>`;

  $("r-flags").innerHTML = pairs.length
    ? pairs.map(([a, b, r]) => `<div class="callout"><strong>${esc(a)}</strong> and <strong>${esc(b)}</strong> are highly correlated (${r.toFixed(2)}). They add little diversification and may fall together.</div>`).join("")
    : '<div class="callout good">No pair is above the 0.70 correlation limit.</div>';
}

// ------------------------------------------------------------------ What-if tab
function cloneToWhatIf() {
  $("wf-inputs").innerHTML = "";
  Object.entries(readWeights("assets-inputs")).forEach(([t, w]) => addRow("wf-inputs", t, w, updateWhatIfTotal));
  updateWhatIfTotal();
}

async function runWhatIf() {
  if (!analysis) return showAlert("Run the analysis on your current portfolio first.");
  const weights = readWeights("wf-inputs"), total = sum(weights);
  if (!Object.keys(weights).length) return showAlert("Add at least one what-if holding.");
  if (Math.abs(total - 100) > 0.1) return showAlert(`What-if weights add up to ${total.toFixed(1)}%. They need to total 100%.`);
  showAlert(null);
  const btn = $("wf-run"); btn.disabled = true; btn.textContent = "Comparing…";
  try { whatIf = await api("/risk", { method: "POST", body: { weights, period: "2y" } }); renderWhatIf(analysis, whatIf); }
  catch (e) { showAlert(`What-if failed: ${e.message}`); }
  finally { btn.disabled = false; btn.textContent = "Compare"; }
}

function renderWhatIf(A, B) {
  const d = B.score - A.score;
  $("wf-cur").textContent = A.score; $("wf-cur-tier").textContent = `${A.level} risk`;
  $("wf-alt").textContent = B.score; $("wf-alt-tier").textContent = `${B.level} risk`;
  const dv = $("wf-delta"); dv.textContent = `${d > 0 ? "+" : d < 0 ? "−" : ""}${Math.abs(d)}`; dv.className = `kpi-val ${d < 0 ? "success" : d > 0 ? "danger" : ""}`;
  $("wf-note").textContent = d < 0 ? `Lower risk by ${Math.abs(d)} points` : d > 0 ? `Higher risk by ${d} points` : "No change";

  const f = (X) => X.concentration;
  const rows = [
    ["Risk score", `${A.score} (${A.level})`, `${B.score} (${B.level})`],
    ["Largest holding", `${f(A).top_asset} ${pct(f(A).top_weight)}`, `${f(B).top_asset} ${pct(f(B).top_weight)}`],
    ["Top 3 holdings", pct(f(A).top3_weight), pct(f(B).top3_weight)],
    ["Effective assets", f(A).effective_assets.toFixed(1), f(B).effective_assets.toFixed(1)],
    ["Volatility", pct(A.volatility), pct(B.volatility)],
    ["Worst drawdown", pct(A.max_drawdown), pct(B.max_drawdown)],
    ["Pairs above 0.7", (A.correlated_pairs || []).length, (B.correlated_pairs || []).length],
  ];
  $("wf-body").innerHTML = rows.map(([l, a, b]) => `<tr><td><strong>${l}</strong></td><td>${esc(a)}</td><td class="gold">${esc(b)}</td></tr>`).join("");
  rulesList("wf-cur-rules", A.hits); rulesList("wf-alt-rules", B.hits);

  const dates = A.dates || [], step = Math.max(1, Math.floor(dates.length / 250));
  chart("wfChart", { type: "line", data: { labels: thin(dates, step), datasets: [
    { label: "Current", data: thin(A.drawdown_series || [], step).map((v) => v * 100), borderColor: "#7A7F88", borderWidth: 2, pointRadius: 0 },
    { label: "What-if", data: thin(B.drawdown_series || [], step).map((v) => v * 100), borderColor: C.gold, borderWidth: 2.5, pointRadius: 0 }] },
    options: lineOptions({ legend: true, pct: true }) });
}

function rulesList(id, hits) {
  $(id).innerHTML = hits && hits.length ? hits.map(([p, why]) => `<div class="callout muted"><strong>+${esc(p)}</strong> &nbsp;${esc(why)}</div>`).join("") : '<p class="hint">No rules triggered.</p>';
}

// ------------------------------------------------------------------ AI report
function mdToHtml(src) {
  const inline = (s) => s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  let out = "", list = false;
  for (const raw of esc(src).split("\n")) {
    const t = raw.trim(), b = t.match(/^[-*]\s+(.*)/);
    if (b) { if (!list) { out += "<ul>"; list = true; } out += `<li>${inline(b[1])}</li>`; continue; }
    if (list) { out += "</ul>"; list = false; }
    const h = t.match(/^#{1,4}\s+(.*)/);
    if (h) out += `<h4>${inline(h[1])}</h4>`; else if (t) out += `<p>${inline(t)}</p>`;
  }
  return out + (list ? "</ul>" : "");
}

async function generateReport() {
  if (!analysis) return showAlert("Run the risk analysis first.");
  const btn = $("btn-ai"), box = $("ai-body"), notice = $("ai-notice");
  setBusy(btn, true, "Generating…");
  box.innerHTML = '<p class="muted-text">Writing the report from your risk metrics…</p>';
  notice.hidden = true;
  try {
    // Strip large timeseries/chart arrays to keep request payload compact and avoid TPM rate limit errors
    const { price_series, drawdown_series, dates, ...compactMetrics } = analysis || {};
    const d = await api("/report", { method: "POST", body: { metrics: compactMetrics }, timeout: 90000 });
    lastReport = d.report || "";
    box.innerHTML = mdToHtml(lastReport);
    $("btn-dl").hidden = false;
    const bad = d.unverified_numbers || [];
    notice.hidden = false;
    notice.className = `callout ${bad.length ? "danger" : "good"}`;
    notice.textContent = bad.length
      ? `Check these figures: ${bad.join(", ")} didn't match the engine's metrics.`
      : "Verified: every number in this report matches the engine's output.";
  } catch (e) { box.innerHTML = `<p style="color:${C.danger}">Couldn't generate the report: ${esc(e.message)}</p>`; }
  finally { setBusy(btn, false, "Generate report"); }
}

function downloadReport() {
  if (!analysis || !lastReport) return;
  const A = analysis, c = A.concentration;
  const md = ["# AUREN risk report", "", `**Risk score:** ${A.score} / 100 (${A.level} risk)`, "", "## Score breakdown",
    (A.hits || []).map(([p, w]) => `- +${p} ${w}`).join("\n") || "- No rules triggered", "", "## Key metrics",
    `- Largest holding: ${c.top_asset} (${pct(c.top_weight)})`, `- Top 3 holdings: ${pct(c.top3_weight)}`,
    `- Effective assets: ${c.effective_assets.toFixed(1)}`, `- Volatility: ${pct(A.volatility)}`, `- Worst drawdown: ${pct(A.max_drawdown)}`, "",
    "## AI assessment", lastReport, "", "_Analytics only, not investment advice. Past performance does not predict future results._"].join("\n");
  const url = URL.createObjectURL(new Blob([md], { type: "text/markdown" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: "auren-risk-report.md" });
  document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
}

function renderInspector(A, size) {
  $("json-inspector").textContent = JSON.stringify({
    risk_score: A.score, risk_level: A.level, score_reasons: A.hits, portfolio_value_usd: size,
    holdings_weight: A.normalized_weights, largest_holding: { [A.concentration.top_asset]: A.concentration.top_weight },
    top_3_holdings_weight: A.concentration.top3_weight, concentration_index_hhi: A.concentration.hhi,
    effective_assets: A.concentration.effective_assets, volatility_annualised: A.volatility, max_drawdown: A.max_drawdown,
    worst_historical_periods: A.worst_historical_periods, sector_exposure: A.sector_exposure,
    "correlated_pairs_above_0.7": A.correlated_pairs, scenario_stress_shocks: A.stress,
  }, null, 2);
}
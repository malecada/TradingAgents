"use strict";
const POLL_MS = 30000;
let activeTab = "performance";
let equityChart = null;

function fmtMoney(v) {
  if (v === null || v === undefined) return "—";
  return "$" + Number(v).toLocaleString(undefined, {minimumFractionDigits: 2,
    maximumFractionDigits: 2});
}

async function getJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error("HTTP " + r.status);
  return r.json();
}

function showBanner(msg) {
  const b = document.getElementById("banner");
  b.textContent = msg; b.classList.remove("hidden");
}
function hideBanner() { document.getElementById("banner").classList.add("hidden"); }

function renderTopbar(perf, health) {
  document.getElementById("equity-summary").innerHTML =
    "<div style='font-size:18px;font-weight:700'>" +
    fmtMoney(perf.cards.equity) + "</div>";
  const dot = document.getElementById("status-dot");
  const txt = document.getElementById("status-text");
  const latest = health.timeline[0];
  if (!latest) { dot.className = "dot stale"; txt.textContent = "no cycles yet"; return; }
  const ageH = (Date.now() - Date.parse(latest.start_ts)) / 3.6e6;
  if (latest.status && latest.status !== "ok") {
    dot.className = "dot fail"; txt.textContent = "last cycle FAILED";
  } else if (ageH > 2) {
    dot.className = "dot stale";
    txt.textContent = "stale — last cycle " + ageH.toFixed(1) + "h ago";
  } else {
    dot.className = "dot ok"; txt.textContent = "running";
  }
}

function renderPerformance(d) {
  const c = d.cards;
  let html = "<div class='cards'>" +
    card("Equity", fmtMoney(c.equity)) +
    card("Live Sharpe (ann.)", c.sharpe) +
    card("Max drawdown", (c.max_drawdown * 100).toFixed(1) + "%") +
    card("Holdings", c.open_positions) + "</div>";
  html += "<div class='panel'><h3>Equity curve · backtest anchor SR " +
    d.backtest_anchor_sharpe + "</h3>";
  html += d.equity.length
    ? "<canvas id='equity-canvas' height='90'></canvas>"
    : "<p class='muted'>No equity data yet.</p>";
  html += "</div>";
  const holdingsSub = d.holdings_stale
    ? "<span class='warn'>STALE — live unavailable" +
        (d.holdings_as_of ? " · snapshot as of " + d.holdings_as_of : "") +
        (d.holdings_live_error ? " (" + d.holdings_live_error + ")" : "") +
      "</span>"
    : "live exchange positions";
  html += "<div class='panel'><h3>Current holdings · " + holdingsSub + "</h3>";
  if (d.holdings.length) {
    html += "<table><tr><th>Coin</th><th>Position qty</th><th>Value (USD)</th></tr>";
    for (const p of d.holdings) {
      html += "<tr><td>" + p.coin + "</td><td>" + p.qty + "</td><td>" +
        (p.usd == null ? "—" : fmtMoney(p.usd)) + "</td></tr>";
    }
    html += "<tr><td><strong>Total</strong></td><td></td><td><strong>" +
      fmtMoney(d.holdings_usd_total) + "</strong></td></tr>";
    html += "</table>";
  } else { html += "<p class='muted'>No open positions.</p>"; }
  html += "</div>";
  document.getElementById("content").innerHTML = html;
  if (d.equity.length) drawEquity(d.equity);
}

function drawEquity(equity) {
  const ctx = document.getElementById("equity-canvas").getContext("2d");
  if (equityChart) equityChart.destroy();
  equityChart = new Chart(ctx, {
    type: "line",
    data: { labels: equity.map(p => p.ts),
            datasets: [{ label: "Live equity", data: equity.map(p => p.value),
              borderColor: "#3fb950", tension: 0.2, pointRadius: 0 }] },
    options: { plugins: { legend: { display: false } },
      scales: { x: { ticks: { color: "#8b949e" } },
                y: { ticks: { color: "#8b949e" } } } }
  });
}

function renderExecutions(d) {
  let html = "<div class='panel'><h3>Execution log</h3>";
  html += d.executions.length ? executionTable(d.executions)
    : "<p class='muted'>No executions yet.</p>";
  html += "</div>";
  document.getElementById("content").innerHTML = html;
}

function statusClass(status) {
  if (status === "FAILED") return "failv";
  if (status === "UNPROTECTED") return "warn";
  return "muted";
}

function executionTable(rows) {
  let h = "<table><tr><th>Cycle</th><th>Coin</th><th>Side</th><th>Qty</th>" +
    "<th>Entry price</th><th>Value (USD)</th><th>Slippage</th><th>Status</th></tr>";
  for (const t of rows) {
    const val = (t.qty != null && t.entry_price != null)
      ? t.qty * t.entry_price : null;
    h += "<tr><td>" + t.cycle_id + "</td><td>" + t.coin + "</td><td>" +
      (t.side || "—") + "</td><td>" + (t.qty ?? "—") + "</td><td>" +
      (t.entry_price ?? "—") + "</td><td>" +
      (val == null ? "—" : fmtMoney(val)) + "</td><td>" +
      (t.slippage ?? "—") +
      "</td><td class='" + statusClass(t.status) + "'>" +
      (t.status || "—") + "</td></tr>";
  }
  return h + "</table>";
}

async function renderDecisions() {
  const { cycles } = await getJSON("/api/cycles");
  if (!cycles.length) {
    document.getElementById("content").innerHTML =
      "<div class='panel'><p class='muted'>No cycles logged yet.</p></div>";
    return;
  }
  let html = "<div class='panel'><h3>Cycle</h3><select id='cycle-pick'>";
  for (const c of cycles) {
    html += "<option value='" + c.cycle_id + "'>" + c.cycle_id +
      " — " + c.start_ts + "</option>";
  }
  html += "</select></div><div id='cycle-detail'></div>";
  document.getElementById("content").innerHTML = html;
  const pick = document.getElementById("cycle-pick");
  pick.addEventListener("change", () => loadCycleDetail(pick.value));
  loadCycleDetail(cycles[0].cycle_id);
}

async function loadCycleDetail(cycleId) {
  const d = await getJSON("/api/cycle/" + encodeURIComponent(cycleId));
  let html = "<div class='panel'><h3>Predictions</h3>";
  html += d.predictions.length
    ? table(d.predictions, ["coin", "horizon", "pred_value",
        "pred_quantile_low", "pred_quantile_high", "ref_price",
        "consensus_signal", "bundle_route"])
    : "<p class='muted'>No predictions.</p>";
  html += "</div><div class='panel'><h3>Sizing</h3>";
  html += d.sizing.length
    ? table(d.sizing, ["coin", "realized_vol", "target_vol", "kelly",
        "confidence", "leverage", "sma30_multiplier", "final_size_notional"])
    : "<p class='muted'>No sizing.</p>";
  html += "</div><div class='panel'><h3>Risk checks</h3>";
  if (d.risk_checks.length) {
    html += "<table><tr><th>Coin</th><th>Check</th><th>Result</th>" +
      "<th>Value</th><th>Threshold</th><th>Reason</th></tr>";
    for (const r of d.risk_checks) {
      html += "<tr><td>" + (r.coin || "—") + "</td><td>" + r.check_name +
        "</td><td class='" + (r.passed ? "pass'>PASS" : "failv'>FAIL") +
        "</td><td>" + (r.value ?? "—") + "</td><td>" +
        (r.threshold ?? "—") + "</td><td>" + (r.reason || "") +
        "</td></tr>";
    }
    html += "</table>";
  } else { html += "<p class='muted'>No risk checks.</p>"; }
  html += "</div><div class='panel'><h3>Shadow decisions</h3>";
  html += d.shadow_decisions.length
    ? table(d.shadow_decisions, ["coin", "live_signal", "backtest_signal",
        "agree", "live_size", "backtest_size", "size_delta_pct"])
    : "<p class='muted'>No shadow decisions.</p>";
  html += "</div>";
  document.getElementById("cycle-detail").innerHTML = html;
}

function renderHealth(d) {
  let html = "<div class='panel'><h3>Cycle timeline</h3>";
  if (d.timeline.length) {
    html += "<table><tr><th>Cycle</th><th>Start</th><th>End</th>" +
      "<th>Status</th><th>Trades</th><th>Stale sources</th></tr>";
    for (const c of d.timeline) {
      html += "<tr><td>" + c.cycle_id + "</td><td>" + c.start_ts +
        "</td><td>" + (c.end_ts || "—") + "</td><td class='" +
        (c.status === "ok" ? "pass'>" : "failv'>") + (c.status || "—") +
        "</td><td>" + (c.n_trades ?? "—") + "</td><td>" +
        (c.supplementary_stale_sources || "—") + "</td></tr>";
    }
    html += "</table>";
  } else { html += "<p class='muted'>No cycles logged yet.</p>"; }
  html += "</div>";
  html += "<div class='panel'><h3>Pipeline steps (latest cycle log)</h3>";
  html += d.steps.length
    ? table(d.steps, ["ts", "step", "status", "duration_ms"])
    : "<p class='muted'>No step records in latest cycle log.</p>";
  html += "</div>";
  html += "<div class='panel'><h3>Recent errors</h3>";
  html += d.errors.length
    ? table(d.errors, ["ts", "cycle_id", "step", "status"])
    : "<p class='muted'>No errors in latest cycle log.</p>";
  html += "</div><div class='panel'><h3>Retrain history</h3>";
  html += d.retrains.length
    ? table(d.retrains, ["retrain_id", "cycle_id", "n_train_rows",
        "train_window_start", "train_dir_acc", "status", "routes"])
    : "<p class='muted'>No retrains yet.</p>";
  html += "</div>";
  document.getElementById("content").innerHTML = html;
}

function table(rows, cols) {
  let h = "<table><tr>";
  for (const c of cols) h += "<th>" + c + "</th>";
  h += "</tr>";
  for (const r of rows) {
    h += "<tr>";
    for (const c of cols) h += "<td>" + (r[c] ?? "—") + "</td>";
    h += "</tr>";
  }
  return h + "</table>";
}

function card(label, value) {
  return "<div class='card'><div class='label'>" + label +
    "</div><div class='value'>" + value + "</div></div>";
}

async function refresh() {
  try {
    const [perf, health] = await Promise.all([
      getJSON("/api/performance"), getJSON("/api/health")]);
    hideBanner();
    renderTopbar(perf, health);
    if (activeTab === "performance") renderPerformance(perf);
    else if (activeTab === "executions") renderExecutions(await getJSON("/api/trades"));
    else if (activeTab === "decisions") await renderDecisions();
    else if (activeTab === "health") renderHealth(health);
  } catch (e) {
    showBanner("Data unavailable: " + e.message + " — retrying…");
  }
}

document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    activeTab = btn.dataset.tab;
    refresh();
  });
});

refresh();
setInterval(refresh, POLL_MS);

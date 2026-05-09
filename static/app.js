let currentTicker = "AAPL";
let currentPeriod = "6mo";
let currentInterval = "1d";

// Clock
function updateClock() {
  const now = new Date();
  const ist = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" }));
  document.getElementById("clock").textContent =
    ist.toLocaleTimeString("en-IN", { hour12: false });
}
setInterval(updateClock, 1000);
updateClock();


// Panel switching
function showPanel(name, el) {
  document.querySelectorAll(".content-panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.getElementById("panel-" + name).classList.add("active");
  if (el) el.classList.add("active");

  if (name === "india")     loadIndia();
  if (name === "news")      loadNews();
  if (name === "macro")     loadMacro();
  if (name === "portfolio") loadPortfolio();
}

// Format numbers
function fmt(n) {
  if (n === null || n === undefined) return "N/A";
  if (Math.abs(n) >= 1e12) return (n / 1e12).toFixed(2) + "T";
  if (Math.abs(n) >= 1e9)  return (n / 1e9).toFixed(2) + "B";
  if (Math.abs(n) >= 1e6)  return (n / 1e6).toFixed(2) + "M";
  return Number(n).toLocaleString();
}

// Watchlist
async function loadWatchlist() {
  const res = await fetch("/api/watchlist");
  const data = await res.json();
  const tape = data.map(s =>
    `<span class="tape-item">
      <span class="tape-sym">${s.symbol.replace(".NS","")}</span>
      ${s.price}
      <span class="${s.change >= 0 ? 'tape-up' : 'tape-dn'}">
        ${s.change >= 0 ? "▲" : "▼"}${Math.abs(s.change)}%
      </span>
    </span>`
  ).join("");
  document.getElementById("tape-inner").innerHTML = tape;

  const list = data.map(s => `
    <div class="ticker-row" onclick="loadTicker('${s.symbol}')">
      <span class="t-sym">${s.symbol.replace(".NS","")}</span>
      <span class="t-price">${s.price}</span>
      <span class="t-chg ${s.change >= 0 ? 'up' : 'dn'}">
        ${s.change >= 0 ? "▲" : "▼"}${Math.abs(s.change)}%
      </span>
    </div>
  `).join("");
  document.getElementById("watchlist-body").innerHTML = list;
}

// Load a ticker (quote + chart + fundamentals + ML)
async function loadTicker(ticker) {
  currentTicker = ticker;
  const [quoteRes, finRes] = await Promise.all([
    fetch(`/api/quote/${ticker}`).then(r => r.json()),
    fetch(`/api/financials/${ticker}`).then(r => r.json()),
  ]);

  renderQuote(quoteRes);
  renderFundamentals(quoteRes, finRes);
  loadChart(ticker, currentPeriod);
  loadMLSignal(ticker);
}

function renderQuote(q) {
  const card = document.getElementById("quote-card");
  card.style.display = "block";
  const chgClass = q.change >= 0 ? "up" : "dn";
  const chgSign  = q.change >= 0 ? "▲" : "▼";

  document.getElementById("quote-header").innerHTML = `
    <div class="quote-name">${q.name} <span style="color:var(--text-dim);font-size:13px">${q.symbol}</span></div>
    <div>
      <span class="quote-price">${q.price}</span>
      <span class="quote-change ${chgClass}">${chgSign} ${Math.abs(q.change)}%</span>
      <span style="color:var(--text-dim);font-size:11px;margin-left:8px">${q.sector}</span>
    </div>
  `;
  document.getElementById("quote-stats").innerHTML = `
    <div class="stats-grid">
      <div class="stat-box"><div class="stat-label">52W HIGH</div><div class="stat-value">${q.week_52_high}</div></div>
      <div class="stat-box"><div class="stat-label">52W LOW</div><div class="stat-value">${q.week_52_low}</div></div>
      <div class="stat-box"><div class="stat-label">VOLUME</div><div class="stat-value">${fmt(q.volume)}</div></div>
      <div class="stat-box"><div class="stat-label">MKT CAP</div><div class="stat-value">${fmt(q.market_cap)}</div></div>
      <div class="stat-box"><div class="stat-label">P/E</div><div class="stat-value">${q.pe_ratio ?? "N/A"}</div></div>
      <div class="stat-box"><div class="stat-label">EPS</div><div class="stat-value">${q.eps ?? "N/A"}</div></div>
      <div class="stat-box"><div class="stat-label">PREV CLOSE</div><div class="stat-value">${q.prev_close}</div></div>
      <div class="stat-box"><div class="stat-label">AVG VOL</div><div class="stat-value">${fmt(q.avg_volume)}</div></div>
    </div>
  `;
}

function renderFundamentals(q, fin) {
  document.getElementById("fundamentals-body").innerHTML = `
    <div class="stats-grid">
      <div class="stat-box"><div class="stat-label">REVENUE</div><div class="stat-value">${fmt(fin.revenue)}</div></div>
      <div class="stat-box"><div class="stat-label">NET INCOME</div><div class="stat-value">${fmt(fin.net_income)}</div></div>
      <div class="stat-box"><div class="stat-label">GROSS PROFIT</div><div class="stat-value">${fmt(fin.gross_profit)}</div></div>
      <div class="stat-box"><div class="stat-label">TOTAL ASSETS</div><div class="stat-value">${fmt(fin.total_assets)}</div></div>
      <div class="stat-box"><div class="stat-label">TOTAL DEBT</div><div class="stat-value">${fmt(fin.total_debt)}</div></div>
      <div class="stat-box"><div class="stat-label">INDUSTRY</div><div class="stat-value" style="font-size:11px">${q.industry}</div></div>
    </div>
  `;
}

function searchTicker() {
  const t = document.getElementById("search-input").value.trim().toUpperCase();
  if (t) loadTicker(t);
}
document.getElementById("search-input").addEventListener("keydown", e => {
  if (e.key === "Enter") searchTicker();
});

async function changePeriod(period, interval, btn) {
  currentPeriod = period;
  currentInterval = interval;
  document.querySelectorAll(".period-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  loadChart(currentTicker, period);
}

// India panel
async function loadIndia() {
  const [idxRes, stkRes] = await Promise.all([
    fetch("/api/india/indices").then(r => r.json()),
    fetch("/api/india/stocks").then(r => r.json()),
  ]);

  document.getElementById("india-indices").innerHTML = `
    <div class="index-card">
      ${idxRes.map(i => `
        <div class="idx-box">
          <div class="idx-name">${i.name}</div>
          <div class="idx-price">${Number(i.price).toLocaleString()}</div>
          <div class="idx-chg ${i.change >= 0 ? 'up' : 'dn'}">${i.change >= 0 ? "▲" : "▼"} ${Math.abs(i.change)}%</div>
        </div>
      `).join("")}
    </div>`;

  document.getElementById("india-stocks").innerHTML = stkRes.map(s => `
    <div class="ticker-row" onclick="loadTicker('${s.symbol}.NS')">
      <span class="t-sym">${s.symbol}</span>
      <span style="color:var(--text-dim);font-size:11px;flex:1;margin-left:8px">${s.name.substring(0,24)}</span>
      <span class="t-price">₹${s.price}</span>
      <span class="t-chg ${s.change >= 0 ? 'up' : 'dn'}">${s.change >= 0 ? "▲" : "▼"}${Math.abs(s.change)}%</span>
    </div>
  `).join("");
}

// News
async function loadNews() {
  const query = document.getElementById("news-query")?.value || "stock market India";
  const data = await fetch(`/api/news?query=${encodeURIComponent(query)}`).then(r => r.json());
  document.getElementById("news-body").innerHTML = data.map(n => `
    <div class="news-item">
      <div class="news-title"><a href="${n.url}" target="_blank">${n.title}</a></div>
      <div class="news-meta">${n.source} &nbsp;|&nbsp; ${n.published}</div>
    </div>
  `).join("");
}

// ML Signal
async function loadMLSignal(ticker) {
  const panel = document.getElementById("ml-signal-panel");
  panel.innerHTML = `
    <div style="color:var(--text-dim);font-size:11px;padding:10px;letter-spacing:1px">
      ⬛ LOADING ML SIGNAL FOR ${ticker}...
    </div>`;

  try {
    const [signalRes, sentimentRes] = await Promise.all([
      fetch(`/api/signal/${ticker}`).then(r => r.json()),
      fetch(`/api/sentiment/${ticker}`).then(r => r.json()),
    ]);
    renderMLPanel(signalRes, sentimentRes, ticker);
  } catch (err) {
    panel.innerHTML = `<div style="color:var(--dn);padding:10px">ML Error: ${err.message}</div>`;
  }
}

function renderMLPanel(signal, sentiment, ticker) {
  const panel = document.getElementById("ml-signal-panel");

  if (signal.signal === "UNAVAILABLE") {
    panel.innerHTML = `<div style="color:var(--dn);padding:10px">
      ML signal unavailable for ${ticker}: ${signal.error || "insufficient data"}
    </div>`;
    return;
  }

  const signalColor = signal.color || "var(--gold)";
  const sentColor =
    sentiment.overall === "POSITIVE" ? "var(--up)" :
    sentiment.overall === "NEGATIVE" ? "var(--dn)" : "var(--gold)";

  const probBars = Object.entries(signal.probabilities || {})
    .map(([label, pct]) => {
      const c = label === "BUY" ? "var(--up)" : label === "SELL" ? "var(--dn)" : "var(--gold)";
      return `
        <div style="margin-bottom:6px">
          <div style="display:flex;justify-content:space-between;font-size:10px;margin-bottom:2px">
            <span style="color:${c}">${label}</span><span>${pct}%</span>
          </div>
          <div style="background:var(--border);height:4px;border-radius:2px">
            <div style="width:${pct}%;height:100%;background:${c};border-radius:2px;transition:width 0.5s"></div>
          </div>
        </div>`;
    }).join("");

  const topFeatures = (signal.top_features || [])
    .map(f => `
      <div style="display:flex;justify-content:space-between;padding:3px 0;
                  border-bottom:1px solid var(--border);font-size:11px">
        <span style="color:var(--text-dim)">${f.feature}</span>
        <span style="color:var(--gold)">${f.importance}%</span>
      </div>`
    ).join("");

  panel.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px">

      <div style="background:var(--bg3);padding:12px;border-radius:3px;border-top:3px solid ${signalColor}">
        <div style="font-size:10px;color:var(--text-dim);letter-spacing:1px;margin-bottom:6px">ML PREDICTION</div>
        <div style="font-size:32px;font-weight:bold;color:${signalColor}">${signal.signal}</div>
        <div style="font-size:11px;color:var(--text-dim);margin-top:4px">
          Confidence: <span style="color:${signalColor}">${signal.confidence}%</span>
        </div>
        <div style="font-size:10px;color:var(--text-dim);margin-top:2px">
          Model accuracy: ${signal.model_accuracy}%
        </div>
      </div>

      <div style="background:var(--bg3);padding:12px;border-radius:3px;border-top:3px solid ${sentColor}">
        <div style="font-size:10px;color:var(--text-dim);letter-spacing:1px;margin-bottom:6px">NEWS SENTIMENT</div>
        <div style="font-size:24px;font-weight:bold;color:${sentColor}">${sentiment.overall}</div>
        <div style="font-size:11px;color:var(--text-dim);margin-top:4px">
          Score: <span style="color:${sentColor}">${sentiment.score}</span>
          &nbsp;|&nbsp; ${sentiment.articles_scored} articles
        </div>
        <div style="font-size:10px;color:var(--text-dim);margin-top:2px">
          📈 ${sentiment.breakdown?.POSITIVE || 0}
          &nbsp;😐 ${sentiment.breakdown?.NEUTRAL || 0}
          &nbsp;📉 ${sentiment.breakdown?.NEGATIVE || 0}
        </div>
        <div style="margin-top:8px;max-height:120px;overflow-y:auto">
          ${(sentiment.articles || []).map(a => `
            <div style="padding:3px 0;border-bottom:1px solid var(--border)">
              <a href="${a.url}" target="_blank"
                style="color:${a.sentiment === 'POSITIVE' ? 'var(--up)' : a.sentiment === 'NEGATIVE' ? 'var(--dn)' : 'var(--text-dim)'};
                       font-size:10px;text-decoration:none;line-height:1.4;display:block">
                ${a.title.substring(0, 80)}${a.title.length > 80 ? '...' : ''}
              </a>
              <span style="font-size:9px;color:#555">${a.source} · ${a.published}</span>
            </div>
          `).join('')}
        </div>
      </div>

    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">

      <div style="background:var(--bg3);padding:12px;border-radius:3px">
        <div style="font-size:10px;color:var(--text-dim);letter-spacing:1px;margin-bottom:8px">
          PROBABILITY DISTRIBUTION
        </div>
        ${probBars}
      </div>

      <div style="background:var(--bg3);padding:12px;border-radius:3px">
        <div style="font-size:10px;color:var(--text-dim);letter-spacing:1px;margin-bottom:8px">
          TOP PREDICTIVE FEATURES
        </div>
        ${topFeatures}
      </div>

    </div>

    <div style="text-align:right;margin-top:8px">
      <button onclick="retrainModel('${ticker}')"
        style="background:transparent;border:1px solid var(--border);color:var(--text-dim);
               padding:3px 10px;font-family:'Courier New',monospace;font-size:10px;
               cursor:pointer;border-radius:2px">
        ↻ RETRAIN MODEL
      </button>
    </div>
  `;
}

async function retrainModel(ticker) {
  await fetch(`/api/signal/${ticker}/retrain`);
  setTimeout(() => loadMLSignal(ticker), 5000);
}

// Macro
async function loadMacro() {
  document.getElementById("macro-body").innerHTML =
    `<div style="color:var(--text-dim);padding:10px;letter-spacing:1px">LOADING MACRO DATA...</div>`;

  let data;
  try {
    data = await fetch("/api/macro").then(r => r.json());
  } catch(e) {
    document.getElementById("macro-body").innerHTML =
      `<div style="color:var(--dn);padding:10px">Failed to load macro data.</div>`;
    return;
  }

  if (!data || data.no_key) {
    document.getElementById("macro-body").innerHTML = `
      <div style="padding:20px;line-height:2">
        <div style="color:var(--gold);font-size:13px;margin-bottom:12px">FRED API KEY NOT SET</div>
        <div style="color:var(--text-dim);font-size:12px">
          Get a free key in 30 seconds:<br>
          1. Go to <a href="https://fred.stlouisfed.org/docs/api/api_key.html" target="_blank"
             style="color:var(--blue)">fred.stlouisfed.org</a><br>
          2. Register with your email<br>
          3. Copy your API key<br>
          4. Open <span style="color:var(--gold)">.env</span> and paste:
             <span style="color:var(--gold)">FRED_API_KEY=your_key_here</span><br>
          5. Restart uvicorn — macro data loads instantly after that
        </div>
      </div>`;
    return;
  }

  const labels = {
    US_GDP_GROWTH:       "US GDP Growth %",
    US_CPI:              "US CPI",
    US_UNEMPLOYMENT:     "Unemployment %",
    FED_FUNDS_RATE:      "Fed Funds Rate %",
    US_10Y_YIELD:        "10Y Treasury %",
    US_2Y_YIELD:         "2Y Treasury %",
    VIX:                 "VIX Fear Index",
    US_RETAIL_SALES:     "Retail Sales",
    YIELD_CURVE_SPREAD:  "Yield Curve Spread",
  };

  document.getElementById("macro-body").innerHTML = `
    <div class="stats-grid">
      ${Object.entries(data).map(([key, val]) => {
        const chgColor  = val.change > 0 ? "var(--up)" : val.change < 0 ? "var(--dn)" : "var(--text-dim)";
        const isInverted = key === "YIELD_CURVE_SPREAD" && val.inverted;
        return `
          <div class="stat-box" style="${isInverted ? 'border-top:2px solid var(--dn)' : ''}">
            <div class="stat-label">${labels[key] || key}</div>
            <div class="stat-value" style="${isInverted ? 'color:var(--dn)' : ''}">${val.value ?? "N/A"}</div>
            <div style="font-size:10px;color:${chgColor};margin-top:2px">
              ${val.change !== null ? (val.change > 0 ? "▲" : "▼") + " " + Math.abs(val.change) : ""}
              <span style="color:#555;margin-left:4px">${val.date || ""}</span>
            </div>
          </div>`;
      }).join("")}
    </div>`;
}

// Portfolio
async function loadPortfolio() {
  const data = await fetch("/api/portfolio").then(r => r.json());
  const positions = data.positions || [];
  const summary   = data.summary   || {};

  if (!positions.length) {
    document.getElementById("portfolio-body").innerHTML =
      `<div style="color:var(--text-dim);padding:10px">No positions yet. Add one above.</div>`;
  } else {
    document.getElementById("portfolio-body").innerHTML = `
      <table style="width:100%;border-collapse:collapse;font-size:12px">
        <tr style="color:var(--text-dim);font-size:10px;border-bottom:1px solid var(--border)">
          <th style="text-align:left;padding:4px">TICKER</th>
          <th style="text-align:right;padding:4px">SHARES</th>
          <th style="text-align:right;padding:4px">BUY</th>
          <th style="text-align:right;padding:4px">CUR</th>
          <th style="text-align:right;padding:4px">P&L</th>
          <th style="text-align:right;padding:4px">P&L %</th>
          <th style="text-align:right;padding:4px">ACTION</th>
        </tr>
        ${positions.map(p => `
          <tr style="border-bottom:1px solid #161616">
            <td style="padding:4px;color:var(--gold);font-weight:bold">${p.ticker}</td>
            <td style="padding:4px;text-align:right">${p.shares}</td>
            <td style="padding:4px;text-align:right">${p.buy_price}</td>
            <td style="padding:4px;text-align:right">${p.current_price || p.buy_price}</td>
            <td style="padding:4px;text-align:right;color:${p.pnl >= 0 ? 'var(--up)' : 'var(--dn)'}">
              ${p.pnl >= 0 ? '+' : ''}${p.pnl || 0}
            </td>
            <td style="padding:4px;text-align:right;color:${p.pnl_pct >= 0 ? 'var(--up)' : 'var(--dn)'}">
              ${p.pnl_pct >= 0 ? '+' : ''}${p.pnl_pct || 0}%
            </td>
            <td style="padding:4px;text-align:right">
              <button onclick="removePosition(${p.id})"
                style="background:transparent;border:1px solid var(--dn);color:var(--dn);
                       padding:1px 6px;font-family:'Courier New',monospace;font-size:10px;cursor:pointer">✕</button>
            </td>
          </tr>
        `).join("")}
      </table>`;
  }

  document.getElementById("portfolio-summary").innerHTML = `
    <div class="stats-grid">
      <div class="stat-box"><div class="stat-label">INVESTED</div>
        <div class="stat-value">$${fmt(summary.total_invested)}</div></div>
      <div class="stat-box"><div class="stat-label">CURRENT VALUE</div>
        <div class="stat-value">$${fmt(summary.current_value)}</div></div>
      <div class="stat-box"><div class="stat-label">TOTAL P&L</div>
        <div class="stat-value" style="color:${summary.total_pnl >= 0 ? 'var(--up)' : 'var(--dn)'}">
          ${summary.total_pnl >= 0 ? '+' : ''}$${fmt(summary.total_pnl)}</div></div>
      <div class="stat-box"><div class="stat-label">RETURN %</div>
        <div class="stat-value" style="color:${summary.total_pnl_pct >= 0 ? 'var(--up)' : 'var(--dn)'}">
          ${summary.total_pnl_pct >= 0 ? '+' : ''}${summary.total_pnl_pct}%</div></div>
    </div>`;
}

async function addPosition() {
  const ticker    = document.getElementById("pt-ticker").value.trim().toUpperCase();
  const shares    = parseFloat(document.getElementById("pt-shares").value);
  const buy_price = parseFloat(document.getElementById("pt-price").value);
  const notes     = document.getElementById("pt-notes").value;

  if (!ticker || !shares || !buy_price) {
    alert("Please fill in ticker, shares, and buy price.");
    return;
  }

  await fetch("/api/portfolio/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker, shares, buy_price, notes }),
  });

  document.getElementById("pt-ticker").value  = "";
  document.getElementById("pt-shares").value  = "";
  document.getElementById("pt-price").value   = "";
  document.getElementById("pt-notes").value   = "";
  loadPortfolio();
}

async function removePosition(id) {
  await fetch(`/api/portfolio/${id}`, { method: "DELETE" });
  loadPortfolio();
}

// Backtest
async function runBacktest() {
  const ticker   = document.getElementById("bt-ticker").value.trim().toUpperCase();
  const strategy = document.getElementById("bt-strategy").value;
  const period   = document.getElementById("bt-period").value;

  if (!ticker) { alert("Enter a ticker"); return; }

  document.getElementById("backtest-results").innerHTML =
    `<div style="color:var(--text-dim);padding:10px;letter-spacing:1px">RUNNING BACKTEST FOR ${ticker}...</div>`;

  const data = await fetch(`/api/backtest/${ticker}?strategy=${strategy}&period=${period}`)
    .then(r => r.json());

  if (data.error) {
    document.getElementById("backtest-results").innerHTML =
      `<div style="color:var(--dn);padding:10px">Error: ${data.error}</div>`;
    return;
  }

  const retColor = data.total_return >= 0 ? "var(--up)" : "var(--dn)";
  const bhColor  = data.bh_return   >= 0 ? "var(--up)" : "var(--dn)";

  document.getElementById("backtest-results").innerHTML = `
    <div class="stats-grid">
      <div class="stat-box"><div class="stat-label">STRATEGY RETURN</div>
        <div class="stat-value" style="color:${retColor}">${data.total_return}%</div></div>
      <div class="stat-box"><div class="stat-label">BUY & HOLD RETURN</div>
        <div class="stat-value" style="color:${bhColor}">${data.bh_return}%</div></div>
      <div class="stat-box"><div class="stat-label">FINAL VALUE</div>
        <div class="stat-value">$${fmt(data.final_value)}</div></div>
      <div class="stat-box"><div class="stat-label">WIN RATE</div>
        <div class="stat-value">${data.win_rate}%</div></div>
      <div class="stat-box"><div class="stat-label">TOTAL TRADES</div>
        <div class="stat-value">${data.total_trades}</div></div>
      <div class="stat-box"><div class="stat-label">INITIAL CAPITAL</div>
        <div class="stat-value">$${fmt(data.initial_capital)}</div></div>
    </div>`;

  // Equity curve
  Plotly.newPlot("backtest-chart", [{
    x: data.equity_curve.map(e => e.date),
    y: data.equity_curve.map(e => e.value),
    type: "scatter", mode: "lines",
    line: { color: data.total_return >= 0 ? "#00cc66" : "#ff4444", width: 2 },
    fill: "tozeroy",
    fillcolor: data.total_return >= 0 ? "#00cc6611" : "#ff444411",
    name: "Portfolio Value",
  }], {
    paper_bgcolor: "#111", plot_bgcolor: "#111",
    font: { color: "#888", family: "Courier New", size: 10 },
    xaxis: { gridcolor: "#1e1e1e", type: "category", nticks: 8, tickangle: -45 },
    yaxis: { gridcolor: "#1e1e1e", side: "right" },
    margin: { t: 10, b: 50, l: 10, r: 60 },
    height: 280,
    showlegend: false,
  }, { displayModeBar: false, responsive: true });

  // Trade log
  document.getElementById("backtest-trades").innerHTML = `
    <table style="width:100%;border-collapse:collapse;font-size:11px">
      <tr style="color:var(--text-dim);font-size:10px;border-bottom:1px solid var(--border)">
        <th style="text-align:left;padding:4px">DATE</th>
        <th style="text-align:left;padding:4px">TYPE</th>
        <th style="text-align:right;padding:4px">PRICE</th>
        <th style="text-align:right;padding:4px">P&L</th>
      </tr>
      ${data.trades.map(t => `
        <tr style="border-bottom:1px solid #161616">
          <td style="padding:4px;color:var(--text-dim)">${t.date}</td>
          <td style="padding:4px;color:${t.type === 'BUY' ? 'var(--up)' : 'var(--dn)'}">
            ${t.type}</td>
          <td style="padding:4px;text-align:right">${t.price}</td>
          <td style="padding:4px;text-align:right;color:${(t.pnl||0) >= 0 ? 'var(--up)' : 'var(--dn)'}">
            ${t.pnl ? (t.pnl >= 0 ? '+' : '') + '$' + t.pnl : '-'}</td>
        </tr>
      `).join("")}
    </table>`;
}

// Screener
async function runScreener() {
  document.getElementById("screener-results").innerHTML =
    `<div style="color:var(--text-dim);padding:10px;letter-spacing:1px">SCANNING UNIVERSE...</div>`;

  const params = new URLSearchParams();
  const minPE     = document.getElementById("sc-min-pe").value;
  const maxPE     = document.getElementById("sc-max-pe").value;
  const minChange = document.getElementById("sc-min-change").value;
  const maxChange = document.getElementById("sc-max-change").value;

  if (minPE)     params.append("min_pe",     minPE);
  if (maxPE)     params.append("max_pe",     maxPE);
  if (minChange) params.append("min_change", minChange);
  if (maxChange) params.append("max_change", maxChange);

  const data = await fetch(`/api/screener?${params}`).then(r => r.json());

  if (!data.length) {
    document.getElementById("screener-results").innerHTML =
      `<div style="color:var(--text-dim);padding:10px">No stocks matched your filters.</div>`;
    return;
  }

  document.getElementById("screener-results").innerHTML = `
    <table style="width:100%;border-collapse:collapse;font-size:12px">
      <tr style="color:var(--text-dim);font-size:10px;border-bottom:1px solid var(--border)">
        <th style="text-align:left;padding:4px">TICKER</th>
        <th style="text-align:left;padding:4px">NAME</th>
        <th style="text-align:right;padding:4px">PRICE</th>
        <th style="text-align:right;padding:4px">CHANGE</th>
        <th style="text-align:right;padding:4px">P/E</th>
        <th style="text-align:right;padding:4px">MKT CAP</th>
        <th style="text-align:left;padding:4px">SECTOR</th>
      </tr>
      ${data.map(s => `
        <tr style="border-bottom:1px solid #161616;cursor:pointer" onclick="loadTicker('${s.symbol}')">
          <td style="padding:4px;color:var(--gold);font-weight:bold">${s.symbol.replace(".NS","")}</td>
          <td style="padding:4px;color:var(--text-dim);font-size:11px">${s.name}</td>
          <td style="padding:4px;text-align:right">${s.price}</td>
          <td style="padding:4px;text-align:right;color:${s.change >= 0 ? 'var(--up)' : 'var(--dn)'}">
            ${s.change >= 0 ? '▲' : '▼'}${Math.abs(s.change)}%</td>
          <td style="padding:4px;text-align:right">${s.pe_ratio ?? "N/A"}</td>
          <td style="padding:4px;text-align:right">${fmt(s.market_cap)}</td>
          <td style="padding:4px;font-size:11px;color:var(--text-dim)">${s.sector}</td>
        </tr>
      `).join("")}
    </table>`;
}

// Init — must be at the bottom after all functions are defined
loadWatchlist();
loadTicker("AAPL");
loadMLSignal("AAPL");
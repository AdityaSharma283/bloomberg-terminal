
async function loadChart(ticker, period = "6mo") {
  currentTicker = ticker;
  currentPeriod = period;

  document.getElementById("price-chart").innerHTML =
    `<div style="color:var(--text-dim);padding:40px;text-align:center">Loading ${ticker}...</div>`;

  const data = await fetch(`/api/indicators/${ticker}?period=${period}`)
    .then(r => r.json());

  if (data.error) {
    document.getElementById("price-chart").innerHTML =
      `<div style="color:var(--dn);padding:20px">Error: ${data.error}</div>`;
    return;
  }

  renderFullChart(data, ticker);
  renderSignalPanel(data.signals, ticker);
}

function renderFullChart(data, ticker) {
  const traces = [];

  // Candlestick — always present
  traces.push({
    x: data.dates,
    open: data.open, high: data.high,
    low: data.low,   close: data.close,
    type: "candlestick", name: ticker,
    increasing: { line: { color: "#00cc66" }, fillcolor: "#00cc6633" },
    decreasing: { line: { color: "#ff4444" }, fillcolor: "#ff444433" },
    yaxis: "y",
  });

  // Bollinger Bands
  if (data.bb_upper && data.bb_lower && data.bb_mid) {
    traces.push({
      x: data.dates, y: data.bb_upper, type: "scatter", mode: "lines",
      line: { color: "#3a9fd555", width: 1, dash: "dot" },
      name: "BB Upper", yaxis: "y", hoverinfo: "skip",
    });
    traces.push({
      x: data.dates, y: data.bb_lower, type: "scatter", mode: "lines",
      line: { color: "#3a9fd555", width: 1, dash: "dot" },
      fill: "tonexty", fillcolor: "#3a9fd510",
      name: "BB Lower", yaxis: "y", hoverinfo: "skip",
    });
    traces.push({
      x: data.dates, y: data.bb_mid, type: "scatter", mode: "lines",
      line: { color: "#3a9fd533", width: 1 },
      name: "BB Mid", yaxis: "y", hoverinfo: "skip",
    });
  }

  // EMAs
  if (data.ema_20) traces.push({ x: data.dates, y: data.ema_20, type: "scatter", mode: "lines", line: { color: "#e0a02088", width: 1 }, name: "EMA 20", yaxis: "y" });
  if (data.ema_50) traces.push({ x: data.dates, y: data.ema_50, type: "scatter", mode: "lines", line: { color: "#cc44ff88", width: 1 }, name: "EMA 50",  yaxis: "y" });
  if (data.ema_200) traces.push({ x: data.dates, y: data.ema_200, type: "scatter", mode: "lines", line: { color: "#ff884488", width: 1.5 }, name: "EMA 200", yaxis: "y" });

  // Volume
  traces.push({
    x: data.dates, y: data.volume, type: "bar", name: "Volume",
    marker: {
      color: data.close.map((c, i) =>
        i === 0 ? "#444" : c >= data.close[i-1] ? "#00cc6644" : "#ff444444"
      ),
    },
    yaxis: "y2",
  });

  // RSI
  if (data.rsi) {
    traces.push({ x: data.dates, y: data.rsi, type: "scatter", mode: "lines", line: { color: "#e0a020", width: 1.5 }, name: "RSI", xaxis: "x", yaxis: "y3" });
    traces.push({ x: [data.dates[0], data.dates[data.dates.length-1]], y: [70, 70], type: "scatter", mode: "lines", line: { color: "#ff444466", width: 1, dash: "dash" }, name: "OB", xaxis: "x", yaxis: "y3", hoverinfo: "skip" });
    traces.push({ x: [data.dates[0], data.dates[data.dates.length-1]], y: [30, 30], type: "scatter", mode: "lines", line: { color: "#00cc6666", width: 1, dash: "dash" }, name: "OS", xaxis: "x", yaxis: "y3", hoverinfo: "skip" });
  }

  // MACD
  if (data.macd && data.macd_signal && data.macd_hist) {
    traces.push({ x: data.dates, y: data.macd_hist, type: "bar", marker: { color: data.macd_hist.map(v => v >= 0 ? "#00cc6666" : "#ff444466") }, name: "Histogram", xaxis: "x", yaxis: "y4" });
    traces.push({ x: data.dates, y: data.macd, type: "scatter", mode: "lines", line: { color: "#3a9fd5", width: 1.5 }, name: "MACD", xaxis: "x", yaxis: "y4" });
    traces.push({ x: data.dates, y: data.macd_signal, type: "scatter", mode: "lines", line: { color: "#ff8844", width: 1.5 }, name: "Signal", xaxis: "x", yaxis: "y4" });
  }

  const layout = {
    paper_bgcolor: "#111", plot_bgcolor: "#111",
    font: { color: "#888", family: "Courier New", size: 10 },
    xaxis:  { gridcolor: "#1e1e1e", rangeslider: { visible: false }, type: "category", nticks: 10, tickangle: -45 },
    yaxis:  { gridcolor: "#1e1e1e", domain: [0.45, 1.0],  side: "right" },
    yaxis2: { gridcolor: "#1e1e1e", domain: [0.30, 0.44], side: "right" },
    yaxis3: { gridcolor: "#1e1e1e", domain: [0.15, 0.29], side: "right", range: [0, 100] },
    yaxis4: { gridcolor: "#1e1e1e", domain: [0.00, 0.14], side: "right" },
    margin: { t: 10, b: 40, l: 10, r: 55 },
    showlegend: true,
    legend: { bgcolor: "#111", font: { size: 9, color: "#888" }, orientation: "h", y: 1.02 },
    height: 600,
  };

  Plotly.newPlot("price-chart", traces, layout, { displayModeBar: false, responsive: true });
}

function renderSignalPanel(signals, ticker) {
  const panel = document.getElementById("ta-signal-panel");

  if (!signals || Object.keys(signals).length === 0) {
    panel.innerHTML = `<div style="color:var(--text-dim);padding:10px">
      Not enough data for signals on this timeframe. Try 3M or longer.
    </div>`;
    return;
  }

  const rsiValue  = signals.rsi_value ?? "N/A";
  const rsiSignal = signals.rsi_signal ?? "Insufficient data";
  const macdSig   = signals.macd_signal ?? "Insufficient data";
  const bbSig     = signals.bb_signal ?? "Insufficient data";

  const rsiColor =
    typeof rsiValue === "number" && rsiValue < 30 ? "var(--up)" :
    typeof rsiValue === "number" && rsiValue > 70 ? "var(--dn)" :
    "var(--gold)";

  const macdColor = macdSig.startsWith("BULLISH") ? "var(--up)" : "var(--dn)";
  const rsiBar    = typeof rsiValue === "number" ? Math.round(rsiValue) : 50;

  panel.innerHTML = `
    <div style="font-size:10px;color:var(--text-dim);margin-bottom:8px;letter-spacing:1px">
      ${ticker} — updated ${new Date().toLocaleTimeString()}
    </div>
    <div class="signal-grid">
      <div class="signal-box">
        <div class="signal-label">RSI (14)</div>
        <div class="signal-value" style="color:${rsiColor}">${rsiValue}</div>
        <div class="rsi-bar-track">
          <div class="rsi-bar-fill" style="width:${rsiBar}%;background:${rsiColor}"></div>
          <div class="rsi-bar-ob"></div>
          <div class="rsi-bar-os"></div>
        </div>
        <div class="signal-desc">${rsiSignal}</div>
      </div>
      <div class="signal-box">
        <div class="signal-label">MACD (12/26/9)</div>
        <div class="signal-value" style="color:${macdColor}">
          ${macdSig.startsWith("BULLISH") ? "▲ BULLISH" : "▼ BEARISH"}
        </div>
        <div class="signal-desc">${macdSig}</div>
      </div>
      <div class="signal-box">
        <div class="signal-label">BOLLINGER BANDS (20,2)</div>
        <div class="signal-value" style="color:var(--blue)">BB</div>
        <div class="signal-desc">${bbSig}</div>
      </div>
    </div>
  `;
}
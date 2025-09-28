const API_BASE = "http://127.0.0.1:8000"; // troque para o endpoint do API Gateway em produção

async function fetchSymbols() {
  const res = await fetch(`${API_BASE}/symbols`);
  const data = await res.json();
  return data.symbols || [];
}

async function fetchLatest(symbol, interval = "5m", limit = 120) {
  const res = await fetch(`${API_BASE}/latest?symbol=${symbol}&interval=${interval}&limit=${limit}`);
  return await res.json();
}

async function fetchPredict(symbol) {
  const res = await fetch(`${API_BASE}/predict?symbol=${symbol}`, { method: "POST" });
  return await res.json();
}

function renderChart(data) {
  const times = data.candles.map(c => c.timestamp);
  const open = data.candles.map(c => c.open);
  const high = data.candles.map(c => c.high);
  const low = data.candles.map(c => c.low);
  const close = data.candles.map(c => c.close);

  const trace = {
    x: times, open, high, low, close, type: "candlestick"
  };

  Plotly.newPlot('chart', [trace], {
    margin: { t: 30, r: 10, b: 40, l: 50 },
    xaxis: { rangeslider: { visible: false } }
  });
}

function renderPrediction(pred, symbol) {
  const el = document.getElementById("prediction");
  el.textContent = `[${symbol}] prob_up=${(pred.prob_up * 100).toFixed(1)}% → ${pred.signal.toUpperCase()} (as of ${pred.asof})`;
}

async function init() {
  const symSel = document.getElementById("symbol");
  const syms = await fetchSymbols();
  syms.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s; opt.textContent = s;
    symSel.appendChild(opt);
  });
  symSel.value = syms[0];

  async function refresh() {
    const s = symSel.value;
    const latest = await fetchLatest(s);
    renderChart(latest);
    const pred = await fetchPredict(s);
    renderPrediction(pred, s);
  }

  document.getElementById("refresh").addEventListener("click", refresh);
  await refresh();
}

init();

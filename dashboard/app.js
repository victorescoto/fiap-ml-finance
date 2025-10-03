// API Configuration - should be set via environment variable in production
const API_BASE = window.API_BASE || "https://d8sxgxjgl9.execute-api.us-east-2.amazonaws.com";

let currentSymbol = null;
let currentData = null;

// Utility functions
function showLoading(show = true) {
  const overlay = document.getElementById('loadingOverlay');
  if (overlay) {
    overlay.classList.toggle('hidden', !show);
  }
}

function showNotification(message, type = 'info') {
  console.log(`${type.toUpperCase()}: ${message}`);
  // Could add toast notifications here
}

function formatNumber(num, decimals = 2) {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
  return num.toFixed(decimals);
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(value);
}

// API functions
async function fetchSymbols() {
  try {
    const res = await fetch(`${API_BASE}/symbols`);
    const data = await res.json();
    return data.symbols || [];
  } catch (error) {
    console.error('Error fetching symbols:', error);
    showNotification('Error loading symbols', 'error');
    return [];
  }
}

async function fetchLatest(symbol, interval = "5m", limit = 120) {
  try {
    const res = await fetch(`${API_BASE}/latest?symbol=${symbol}&interval=${interval}&limit=${limit}`);
    const data = await res.json();
    return data;
  } catch (error) {
    console.error('Error fetching latest data:', error);
    showNotification('Error loading market data', 'error');
    return null;
  }
}

async function fetchPredict(symbol) {
  try {
    const res = await fetch(`${API_BASE}/predict?symbol=${symbol}`, { method: "POST" });
    const data = await res.json();
    return data;
  } catch (error) {
    console.error('Error fetching prediction:', error);
    showNotification('Error generating prediction', 'error');
    return null;
  }
}

// UI Update functions
function updateStatsCards(currentPrice, change, volume, confidence = null) {
  // Update current price
  const priceElement = document.getElementById('currentPrice');
  if (priceElement) {
    priceElement.textContent = currentPrice !== null ? formatCurrency(currentPrice) : '$--';
  }

  // Update daily change
  const changeElement = document.getElementById('dailyChange');
  const changeIcon = document.getElementById('changeIcon');
  if (changeElement && changeIcon) {
    if (change !== null) {
      const isPositive = change >= 0;
      changeElement.textContent = `${isPositive ? '+' : ''}${change.toFixed(2)}%`;
      changeElement.classList.toggle('text-green-400', isPositive);
      changeElement.classList.toggle('text-red-400', !isPositive);
      changeElement.classList.remove('text-slate-400');
      
      changeIcon.classList.toggle('text-green-400', isPositive);
      changeIcon.classList.toggle('text-red-400', !isPositive);
      changeIcon.classList.remove('text-slate-400');
      changeIcon.setAttribute('data-lucide', isPositive ? 'trending-up' : 'trending-down');
    } else {
      changeElement.textContent = '--%';
      changeElement.classList.remove('text-green-400', 'text-red-400');
      changeElement.classList.add('text-slate-400');
      
      changeIcon.classList.remove('text-green-400', 'text-red-400');
      changeIcon.classList.add('text-slate-400');
      changeIcon.setAttribute('data-lucide', 'minus');
    }
    lucide.createIcons();
  }

  // Update volume
  const volumeElement = document.getElementById('volume');
  if (volumeElement) {
    volumeElement.textContent = volume !== null ? formatNumber(volume) : '--';
  }

  // Update confidence if provided
  const confidenceElement = document.getElementById('confidence');
  if (confidenceElement && confidence !== null) {
    confidenceElement.textContent = `${Math.round(confidence)}%`;
  }
}

function renderChart(data) {
  if (!data || !data.candles || data.candles.length === 0) {
    showNoDataMessage();
    return;
  }

  const times = data.candles.map(c => c.timestamp);
  const opens = data.candles.map(c => c.open);
  const highs = data.candles.map(c => c.high);
  const lows = data.candles.map(c => c.low);
  const closes = data.candles.map(c => c.close);
  const volumes = data.candles.map(c => c.volume || 0);

  // Update stats cards
  if (closes.length > 0) {
    const currentPrice = closes[closes.length - 1];
    const previousPrice = closes.length > 1 ? closes[closes.length - 2] : currentPrice;
    const change = previousPrice !== 0 ? ((currentPrice - previousPrice) / previousPrice * 100) : 0;
    const totalVolume = volumes.reduce((a, b) => a + b, 0);
    updateStatsCards(currentPrice, change, totalVolume);
  }

  // Use real data for the chart
  const trace_line = {
    x: times,
    y: closes,
    type: "scatter",
    mode: "lines",
    name: "Price",
    line: { color: "#3B82F6", width: 2 },
    showlegend: false
  };

  const layout = {
    title: {
      text: `${data.symbol || currentSymbol || 'Stock'} - ${data.interval} Price Chart`,
      font: { color: "#e2e8f0", size: 18 }
    },
    xaxis: { 
      title: "Time",
      color: "#94a3b8",
      gridcolor: "#374151",
      showgrid: true
    },
    yaxis: { 
      title: "Price ($)",
      color: "#94a3b8",
      gridcolor: "#374151",
      showgrid: true
    },
    plot_bgcolor: "rgba(15, 23, 42, 0.8)",
    paper_bgcolor: "transparent",
    font: { color: "#e2e8f0" },
    margin: { l: 60, r: 60, t: 60, b: 60 },
    showlegend: false
  };

  const config = {
    responsive: true,
    displayModeBar: false
  };

  Plotly.newPlot("chart", [trace_line], layout, config);
}

function showNoDataMessage() {
  const chartDiv = document.getElementById('chart');
  chartDiv.innerHTML = `
    <div class="flex flex-col items-center justify-center h-full text-slate-400 space-y-4">
      <i data-lucide="alert-circle" class="w-16 h-16 text-slate-500"></i>
      <div class="text-center">
        <h3 class="text-lg font-medium text-slate-300 mb-2">No Data Available</h3>
        <p class="text-sm text-slate-400 mb-4">
          Unable to load market data for ${currentSymbol || 'this symbol'}.
        </p>
        <button 
          onclick="loadData()" 
          class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors duration-200 flex items-center space-x-2 mx-auto"
        >
          <i data-lucide="refresh-cw" class="w-4 h-4"></i>
          <span>Try Again</span>
        </button>
      </div>
    </div>
  `;
  
  // Re-initialize lucide icons for the new content
  lucide.createIcons();
  
  // Clear stats cards
  updateStatsCards(null, null, null);
}

function renderPrediction(pred, symbol) {
  const predictionElement = document.getElementById("prediction");
  
  if (!pred) {
    predictionElement.innerHTML = `
      <div class="flex flex-col items-center justify-center py-8 text-slate-400">
        <i data-lucide="alert-triangle" class="w-12 h-12 text-slate-500 mb-4"></i>
        <h3 class="text-lg font-medium text-slate-300 mb-2">Prediction Failed</h3>
        <p class="text-sm text-slate-400 mb-4 text-center">
          Unable to generate prediction for ${symbol || 'this symbol'}.<br>
          Please try again or check if the symbol is valid.
        </p>
        <button 
          onclick="makePrediction()" 
          class="bg-emerald-600 hover:bg-emerald-700 px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors duration-200 flex items-center space-x-2"
        >
          <i data-lucide="refresh-cw" class="w-4 h-4"></i>
          <span>Try Again</span>
        </button>
      </div>
    `;
    lucide.createIcons();
    return;
  }
  
  const confidence = pred.prob_up * 100;
  const signal = pred.signal?.toUpperCase() || 'HOLD';
  const isPositive = signal === 'BUY' || confidence > 60;
  
  // Update confidence in stats card
  updateStatsCards(null, null, null, confidence);

  predictionElement.innerHTML = `
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="bg-slate-700/30 rounded-lg p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">Signal</h3>
          <div class="px-3 py-1 rounded-full text-sm font-medium ${
            isPositive ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }">
            ${signal}
          </div>
        </div>
        <div class="flex items-center space-x-3">
          <i data-lucide="${isPositive ? 'trending-up' : 'trending-down'}" 
             class="w-8 h-8 ${isPositive ? 'text-green-400' : 'text-red-400'}"></i>
          <div>
            <p class="text-2xl font-bold text-white">${confidence.toFixed(1)}%</p>
            <p class="text-sm text-slate-400">Confidence</p>
          </div>
        </div>
      </div>
      
      <div class="bg-slate-700/30 rounded-lg p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">Details</h3>
          <i data-lucide="info" class="w-5 h-5 text-blue-400"></i>
        </div>
        <div class="space-y-2">
          <div class="flex justify-between">
            <span class="text-slate-400">Symbol:</span>
            <span class="text-white font-medium">${symbol}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-400">Confidence:</span>
            <span class="text-white">${confidence.toFixed(1)}%</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-400">Generated:</span>
            <span class="text-white">${prediction.asof || new Date().toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  `;
  
  lucide.createIcons();
}

// Main functions
async function loadData() {
  const symbolSelect = document.getElementById('symbolSelect');
  const intervalSelect = document.getElementById('intervalSelect');
  
  if (!symbolSelect.value || symbolSelect.value === 'Loading symbols...') {
    showNotification('Please select a symbol first', 'warning');
    return;
  }

  currentSymbol = symbolSelect.value;
  const interval = intervalSelect.value;

  showLoading(true);
  
  try {
    const data = await fetchLatest(currentSymbol, interval, 120);
    currentData = data;
    
    renderChart(data);
    showNotification('Data loaded successfully', 'success');
  } catch (error) {
    console.error('Error loading data:', error);
    renderChart(null); // Will show no data message
    showNotification('Failed to load market data', 'error');
  } finally {
    showLoading(false);
  }
}

async function makePrediction() {
  const symbolSelect = document.getElementById('symbolSelect');
  
  if (!symbolSelect.value || symbolSelect.value === 'Loading symbols...') {
    showNotification('Please select a symbol first', 'warning');
    return;
  }

  const selectedSymbol = symbolSelect.value;
  showLoading(true);
  
  try {
    const prediction = await fetchPredict(selectedSymbol);
    renderPrediction(prediction, selectedSymbol);
    showNotification('Prediction generated successfully', 'success');
  } catch (error) {
    console.error('Error making prediction:', error);
    renderPrediction(null, selectedSymbol);
    showNotification('Error generating prediction', 'error');
  } finally {
    showLoading(false);
  }
}

// Initialize the application
async function init() {
  try {
    showLoading(true);
    
    // Load symbols
    const symbols = await fetchSymbols();
    const symbolSelect = document.getElementById('symbolSelect');
    
    // Clear loading option
    symbolSelect.innerHTML = '';
    
    if (symbols.length === 0) {
      // Use default symbols if API fails
      const defaultSymbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'];
      defaultSymbols.forEach(symbol => {
        const option = document.createElement('option');
        option.value = symbol;
        option.textContent = symbol;
        symbolSelect.appendChild(option);
      });
      currentSymbol = defaultSymbols[0];
    } else {
      symbols.forEach(symbol => {
        const option = document.createElement('option');
        option.value = symbol;
        option.textContent = symbol;
        symbolSelect.appendChild(option);
      });
      currentSymbol = symbols[0];
    }
    
    symbolSelect.value = currentSymbol;
    
    // Add event listeners to auto-load data when selects change
    symbolSelect.addEventListener('change', () => {
      loadData();
    });
    
    const intervalSelect = document.getElementById('intervalSelect');
    intervalSelect.addEventListener('change', () => {
      loadData();
    });
    
    showNotification('Dashboard initialized successfully', 'success');
    
    // Auto-load data for first symbol
    await loadData();
    
  } catch (error) {
    console.error('Error initializing dashboard:', error);
    showNotification('Dashboard initialized with sample data', 'info');
  } finally {
    showLoading(false);
  }
}

// Start the application
document.addEventListener('DOMContentLoaded', init);

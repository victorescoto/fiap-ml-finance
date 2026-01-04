// FIAP Tech Challenge - Fase 4: LSTM Dashboard App
// API Configuration
const API_BASE = window.API_BASE || "http://localhost:8000";

let currentSymbol = null;
let currentData = null;
let currentPredictions = null;

// Utility functions
function showLoading(show = true) {
  const overlay = document.getElementById('loadingOverlay');
  if (overlay) {
    overlay.classList.toggle('hidden', !show);
  }
}

function showNotification(message, type = 'info') {
  console.log(`${type.toUpperCase()}: ${message}`);
  // Add visual notification system if needed
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(value);
}

function formatPercentage(value) {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function getConfidenceColor(confidence) {
  switch (confidence) {
    case 'very_high': return 'text-green-400';
    case 'high': return 'text-blue-400';
    case 'medium': return 'text-yellow-400';
    case 'low': return 'text-orange-400';
    case 'very_low': return 'text-red-400';
    default: return 'text-slate-400';
  }
}

function getConfidenceLabel(confidence) {
  switch (confidence) {
    case 'very_high': return 'Very High';
    case 'high': return 'High';
    case 'medium': return 'Medium';
    case 'low': return 'Low';
    case 'very_low': return 'Very Low';
    default: return 'Unknown';
  }
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

async function fetchHistoricalData(symbol, period = '6mo') {
  try {
    const res = await fetch(`${API_BASE}/historical/${symbol}?period=${period}`);
    const data = await res.json();
    return data;
  } catch (error) {
    console.error('Error fetching historical data:', error);
    showNotification('Error loading historical data', 'error');
    return null;
  }
}

async function predictPrices(symbol, days = 3) {
  try {
    showLoading(true);
    const res = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        symbol: symbol,
        days: days,
        confidence_interval: false
      })
    });
    const data = await res.json();
    showLoading(false);
    return data;
  } catch (error) {
    console.error('Error predicting prices:', error);
    showNotification('Error making predictions', 'error');
    showLoading(false);
    return null;
  }
}

async function trainModel(symbol) {
  try {
    showLoading(true);
    showNotification('Training model... This may take a few minutes', 'info');
    const res = await fetch(`${API_BASE}/train`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        symbol: symbol,
        start_date: "2020-01-01",
        retrain: false
      })
    });
    const data = await res.json();
    showLoading(false);
    
    if (data.status === 'success') {
      showNotification('Model trained successfully!', 'success');
    } else if (data.status === 'exists') {
      showNotification('Model already exists', 'info');
    } else {
      showNotification(data.message || 'Training failed', 'error');
    }
    
    return data;
  } catch (error) {
    console.error('Error training model:', error);
    showNotification('Error training model', 'error');
    showLoading(false);
    return null;
  }
}

async function fetchModelStatus() {
  try {
    const res = await fetch(`${API_BASE}/models`);
    const data = await res.json();
    return data;
  } catch (error) {
    console.error('Error fetching model status:', error);
    return [];
  }
}

// UI Update Functions
function updateStatusCards(data) {
  if (data && data.current_price) {
    document.getElementById('currentPrice').textContent = formatCurrency(data.current_price);
    
    if (data.predicted_prices && data.predicted_prices.length > 0) {
      const firstPrediction = data.predicted_prices[0];
      const changeColor = firstPrediction.change >= 0 ? 'text-green-400' : 'text-red-400';
      document.getElementById('priceChange').innerHTML = 
        `<span class="${changeColor}">${formatPercentage(firstPrediction.change_percent)}</span>`;
    }
  }

  if (data && data.confidence) {
    document.getElementById('modelStatus').textContent = 
      data.model_info ? data.model_info.model_type : 'LSTM';
    document.getElementById('modelConfidence').innerHTML = 
      `<span class="${getConfidenceColor(data.confidence)}">${getConfidenceLabel(data.confidence)}</span>`;
  }

  if (data && data.model_metrics) {
    const mape = data.model_metrics.MAPE;
    if (mape) {
      document.getElementById('mapeScore').textContent = `${mape.toFixed(2)}%`;
      document.getElementById('mapeLabel').innerHTML = 
        `<span class="${getConfidenceColor(data.confidence)}">Accuracy</span>`;
    }
  }

  if (data && data.model_info && data.model_info.training_data) {
    document.getElementById('trainingData').textContent = 
      Math.round(data.model_info.training_data).toLocaleString();
  }
}

function updatePriceChart(historicalData, predictions) {
  const container = document.getElementById('priceChart');
  
  if (!historicalData || !historicalData.data) {
    container.innerHTML = '<p class="text-slate-400 text-center py-8">No historical data available</p>';
    return;
  }

  // Prepare historical data
  const dates = historicalData.data.map(d => d.date);
  const prices = historicalData.data.map(d => d.close);

  const traces = [
    {
      x: dates,
      y: prices,
      type: 'scatter',
      mode: 'lines',
      name: 'Historical Prices',
      line: {
        color: '#3B82F6',
        width: 2
      }
    }
  ];

  // Add predictions if available
  if (predictions && predictions.predicted_prices) {
    const predDates = predictions.predicted_prices.map(p => p.date);
    const predPrices = predictions.predicted_prices.map(p => p.predicted_price);
    
    // Connect last historical price with first prediction
    const connectionDates = [dates[dates.length - 1], predDates[0]];
    const connectionPrices = [prices[prices.length - 1], predPrices[0]];

    traces.push({
      x: connectionDates,
      y: connectionPrices,
      type: 'scatter',
      mode: 'lines',
      name: 'Transition',
      line: {
        color: '#10B981',
        width: 2,
        dash: 'dot'
      },
      showlegend: false
    });

    traces.push({
      x: predDates,
      y: predPrices,
      type: 'scatter',
      mode: 'lines+markers',
      name: 'LSTM Predictions',
      line: {
        color: '#10B981',
        width: 3
      },
      marker: {
        color: '#10B981',
        size: 6
      }
    });
  }

  const layout = {
    title: {
      text: `${historicalData.symbol} - Price History & LSTM Predictions`,
      font: { color: '#F1F5F9' }
    },
    xaxis: {
      title: 'Date',
      color: '#94A3B8',
      gridcolor: '#334155'
    },
    yaxis: {
      title: 'Price (USD)',
      color: '#94A3B8',
      gridcolor: '#334155',
      tickformat: '$,.2f'
    },
    plot_bgcolor: 'transparent',
    paper_bgcolor: 'transparent',
    font: { color: '#F1F5F9' },
    legend: {
      bgcolor: 'rgba(30, 41, 59, 0.8)',
      bordercolor: '#475569',
      borderwidth: 1
    },
    margin: { l: 60, r: 20, t: 60, b: 60 }
  };

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'autoScale2d']
  };

  Plotly.newPlot(container, traces, layout, config);
}

function updatePredictionsTable(predictions) {
  const container = document.getElementById('predictionsTable');
  
  if (!predictions || !predictions.predicted_prices) {
    container.innerHTML = '<p class="text-slate-400 text-center py-8">No predictions available</p>';
    return;
  }

  const tableHtml = `
    <div class="overflow-hidden rounded-lg border border-slate-600">
      <table class="w-full">
        <thead class="bg-slate-700">
          <tr>
            <th class="px-4 py-3 text-left text-sm font-medium text-slate-300">Date</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-slate-300">Predicted Price</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-slate-300">Change</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-slate-300">Change %</th>
          </tr>
        </thead>
        <tbody class="bg-slate-800/50 divide-y divide-slate-600">
          ${predictions.predicted_prices.map(pred => {
            const changeColor = pred.change >= 0 ? 'text-green-400' : 'text-red-400';
            return `
              <tr class="hover:bg-slate-700/30 transition-colors">
                <td class="px-4 py-3 text-sm text-white">${new Date(pred.date).toLocaleDateString()}</td>
                <td class="px-4 py-3 text-sm text-white font-medium">${formatCurrency(pred.predicted_price)}</td>
                <td class="px-4 py-3 text-sm ${changeColor}">${formatCurrency(pred.change)}</td>
                <td class="px-4 py-3 text-sm ${changeColor}">${formatPercentage(pred.change_percent)}</td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    </div>
    <div class="mt-4 text-xs text-slate-400">
      <p><strong>Model Confidence:</strong> <span class="${getConfidenceColor(predictions.confidence)}">${getConfidenceLabel(predictions.confidence)}</span></p>
      <p><strong>Prediction Time:</strong> ${new Date(predictions.prediction_date).toLocaleString()}</p>
    </div>
  `;

  container.innerHTML = tableHtml;
}

function updateModelMetrics(predictions) {
  const container = document.getElementById('metricsContainer');
  
  if (!predictions || !predictions.model_metrics) {
    container.innerHTML = '<p class="text-slate-400 text-center py-8">No metrics available</p>';
    return;
  }

  const metrics = predictions.model_metrics;
  const metricsHtml = `
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-slate-700/30 rounded-lg p-4 text-center">
        <div class="text-2xl font-bold text-blue-400">${metrics.MAE?.toFixed(2) || 'N/A'}</div>
        <div class="text-sm text-slate-400 mt-1">Mean Absolute Error</div>
        <div class="text-xs text-slate-500 mt-1">Lower is better</div>
      </div>
      <div class="bg-slate-700/30 rounded-lg p-4 text-center">
        <div class="text-2xl font-bold text-green-400">${metrics.RMSE?.toFixed(2) || 'N/A'}</div>
        <div class="text-sm text-slate-400 mt-1">Root Mean Square Error</div>
        <div class="text-xs text-slate-500 mt-1">Lower is better</div>
      </div>
      <div class="bg-slate-700/30 rounded-lg p-4 text-center">
        <div class="text-2xl font-bold ${getConfidenceColor(predictions.confidence)}">${metrics.MAPE?.toFixed(2) || 'N/A'}%</div>
        <div class="text-sm text-slate-400 mt-1">Mean Absolute Percentage Error</div>
        <div class="text-xs text-slate-500 mt-1">Accuracy indicator</div>
      </div>
    </div>
    <div class="mt-6 bg-slate-700/20 rounded-lg p-4">
      <h4 class="text-sm font-medium text-slate-300 mb-2">Model Information</h4>
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span class="text-slate-400">Model Type:</span>
          <span class="text-white ml-2">${predictions.model_info?.model_type || 'LSTM'}</span>
        </div>
        <div>
          <span class="text-slate-400">Sequence Length:</span>
          <span class="text-white ml-2">${predictions.model_info?.sequence_length || 'N/A'}</span>
        </div>
        <div>
          <span class="text-slate-400">Training Data:</span>
          <span class="text-white ml-2">${predictions.model_info?.training_data || 'N/A'} points</span>
        </div>
        <div>
          <span class="text-slate-400">Confidence:</span>
          <span class="${getConfidenceColor(predictions.confidence)} ml-2">${getConfidenceLabel(predictions.confidence)}</span>
        </div>
      </div>
    </div>
  `;

  container.innerHTML = metricsHtml;
}

// Main Functions
async function loadSymbols() {
  const symbols = await fetchSymbols();
  const select = document.getElementById('symbolSelect');
  
  if (symbols.length === 0) {
    select.innerHTML = '<option>Error loading symbols</option>';
    return;
  }

  select.innerHTML = symbols.map(symbol => 
    `<option value="${symbol}">${symbol}</option>`
  ).join('');

  // Set default symbol
  if (symbols.length > 0) {
    currentSymbol = symbols[0];
    select.value = currentSymbol;
  }
}

async function loadData() {
  if (!currentSymbol) return;

  const period = document.getElementById('periodSelect').value;
  const historicalData = await fetchHistoricalData(currentSymbol, period);
  
  if (historicalData) {
    currentData = historicalData;
    updatePriceChart(historicalData, currentPredictions);
  }
}

async function makePredictions() {
  if (!currentSymbol) return;

  const days = parseInt(document.getElementById('daysSelect').value);
  const predictions = await predictPrices(currentSymbol, days);
  
  if (predictions) {
    currentPredictions = predictions;
    updateStatusCards(predictions);
    updatePredictionsTable(predictions);
    updateModelMetrics(predictions);
    updatePriceChart(currentData, predictions);
  }
}

async function trainModelForSymbol() {
  if (!currentSymbol) return;

  const result = await trainModel(currentSymbol);
  if (result && result.status === 'success') {
    // Automatically make predictions after training
    setTimeout(() => makePredictions(), 1000);
  }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', async function() {
  // Initialize Lucide icons
  lucide.createIcons();
  
  // Load initial data
  await loadSymbols();
  await loadData();
  
  // Setup event listeners
  document.getElementById('symbolSelect').addEventListener('change', function(e) {
    currentSymbol = e.target.value;
    currentPredictions = null; // Clear predictions when symbol changes
    loadData();
    
    // Clear previous predictions
    document.getElementById('predictionsTable').innerHTML = 
      '<p class="text-slate-400 text-center py-8">Select a stock and click "Predict with LSTM" to see predictions</p>';
    document.getElementById('metricsContainer').innerHTML = 
      '<p class="text-slate-400 text-center py-8">Train or select a model to see performance metrics</p>';
    
    // Reset status cards
    document.getElementById('currentPrice').textContent = '--';
    document.getElementById('priceChange').textContent = '--';
    document.getElementById('modelStatus').textContent = '--';
    document.getElementById('modelConfidence').textContent = '--';
    document.getElementById('mapeScore').textContent = '--';
    document.getElementById('trainingData').textContent = '--';
  });

  document.getElementById('periodSelect').addEventListener('change', loadData);
  document.getElementById('predictBtn').addEventListener('click', makePredictions);
  document.getElementById('trainBtn').addEventListener('click', trainModelForSymbol);
  document.getElementById('refreshBtn').addEventListener('click', function() {
    loadData();
    if (currentPredictions) {
      makePredictions();
    }
  });

  // Update last update time
  function updateLastUpdateTime() {
    document.getElementById('lastUpdate').textContent = 
      'Last updated: ' + new Date().toLocaleTimeString();
  }
  
  updateLastUpdateTime();
  setInterval(updateLastUpdateTime, 60000); // Update every minute

  // Test API connection
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (response.ok) {
      document.getElementById('connectionStatus').textContent = 'Connected';
      document.getElementById('connectionStatus').className = 'text-green-400';
    } else {
      throw new Error('API not responding');
    }
  } catch (error) {
    document.getElementById('connectionStatus').textContent = 'Disconnected';
    document.getElementById('connectionStatus').className = 'text-red-400';
    showNotification('API connection failed', 'error');
  }
});
let currentCurrency = 'XRPUSDT';
let avgVolume = 0;
let lastVolume = 0;
let signalHistory = [];
let buySignalIssued = false;
let sellSignalIssued = false;

async function loadCurrencyPairs() {
  try {
    const res = await fetch('https://api.binance.com/api/v3/exchangeInfo');
    const data = await res.json();
    const pairs = data.symbols.filter(symbol => symbol.symbol.endsWith('USDT'));
    const currencySelect = document.getElementById('currency');

    pairs.forEach(pair => {
      const option = document.createElement('option');
      option.value = pair.symbol;
      option.textContent = pair.symbol;
      currencySelect.appendChild(option);
    });

    currencySelect.addEventListener('change', updateCurrency);
    updateCurrency();
  } catch (error) {
    console.error('Error loading currency pairs:', error);
  }
}

function updateCurrency() {
  const currencySelect = document.getElementById('currency');
  currentCurrency = currencySelect.value;
  fetchPrice();
  fetchTrades();
  getAvgVolume();
  updateChart();
}

async function fetchPrice() {
  try {
    const res = await fetch(`https://api.binance.com/api/v3/ticker/price?symbol=${currentCurrency}`);
    const data = await res.json();
    const price = parseFloat(data.price);
    console.log('Price:', price);
    document.getElementById('price').textContent = `${price.toFixed(2)} USDT`;
  } catch (error) {
    console.error('Error fetching price:', error);
  }
}
setInterval(fetchPrice, 5000);

let lastTrades = [];

async function fetchTrades() {
  try {
    const res = await fetch(`https://api.binance.com/api/v3/trades?symbol=${currentCurrency}&limit=50`);
    const data = await res.json();
    lastTrades = data;
    const tradeList = document.getElementById('trades');
    tradeList.innerHTML = '';
    data.forEach(trade => {
      const li = document.createElement('li');
      li.textContent = `قیمت: ${parseFloat(trade.price)} - مقدار: ${parseFloat(trade.qty)} - ${trade.isBuyerMaker ? 'فروش' : 'خرید'}`;
      tradeList.appendChild(li);
    });
    analyzeStrategy();
  } catch (error) {
    console.error('Error fetching trades:', error);
  }
}
setInterval(fetchTrades, 5000);

async function getAvgVolume() {
  try {
    const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${currentCurrency}&interval=1h&limit=200`);
    const data = await res.json();
    const volumes = data.map(candle => parseFloat(candle[5]));
    avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;
    console.log('Average Volume:', avgVolume);
    document.getElementById('avgVolume').textContent = `میانگین حجم: ${avgVolume.toFixed(2)}`;
  } catch (error) {
    console.error('Error fetching average volume:', error);
    document.getElementById('avgVolume').textContent = 'خطا در دریافت حجم!';
  }
}

function analyzeStrategy() {
  let buyCount = 0;
  let sellCount = 0;
  
  // شمارش معاملات خرید و فروش متوالی
  lastTrades.forEach(trade => {
    if (trade.isBuyerMaker) {
      sellCount++;
    } else {
      buyCount++;
    }
  });

  const lastCandle = lastTrades[lastTrades.length - 1];
  const isGreenCandle = parseFloat(lastCandle.price) > parseFloat(lastTrades[lastTrades.length - 2].price);

  if (isGreenCandle && lastVolume > avgVolume && buyCount >= 30 && !buySignalIssued) {
    issueBuySignal();
  } else if (!isGreenCandle && lastVolume > avgVolume && sellCount >= 30 && !sellSignalIssued) {
    issueSellSignal();
  }
}

function issueBuySignal() {
  document.getElementById('signal').textContent = 'سیگنال خرید صادر شد!';
  addSignalToChart('خرید');
  buySignalIssued = true;
  sellSignalIssued = false;
}

function issueSellSignal() {
  document.getElementById('signal').textContent = 'سیگنال فروش صادر شد!';
  addSignalToChart('فروش');
  sellSignalIssued = true;
  buySignalIssued = false;
}

function addSignalToChart(signal) {
  const chartContainer = document.getElementById('chart');
  const price = parseFloat(lastTrades[lastTrades.length - 1].price);
  const label = signal === 'خرید' ? 'خرید' : 'فروش';

  chartContainer.innerHTML += `<div class="signal-label" style="position: absolute; top: 50%; left: ${price}%">${label}</div>`;
}

function updateChart() {
  try {
    new TradingView.widget({
      width: '100%',
      height: '100%',
      symbol: `BINANCE:${currentCurrency}`,
      interval: '60',
      timezone: 'Etc/UTC',
      theme: 'dark',
      style: '1',
      locale: 'fa',
      toolbar_bg: '#f1f3f6',
      allow_symbol_change: true,
      container_id: "chart",
    });
  } catch (error) {
    console.error('Error loading TradingView chart:', error);
  }
}

// شروع بارگذاری جفت ارزها
loadCurrencyPairs();

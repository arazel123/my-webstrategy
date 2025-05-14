let currentCurrency = 'XRPUSDT';
let avgVolume = 0;
let lastKline = null;
let signalChecked = false;
let signalHistory = [];
let buySignalIssued = false;
let sellSignalIssued = false;

// اجرای اولیه
loadCurrencyPairs();
setInterval(fetchPrice, 5000);
setInterval(fetchTrades, 5000);
setInterval(checkCandleClosure, 10000); // هر 10 ثانیه بررسی کندل بسته‌شده

// دریافت لیست جفت ارزها
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
    document.getElementById('price').textContent = `${price.toFixed(2)} USDT`;
  } catch (error) {
    console.error('Error fetching price:', error);
  }
}

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
  } catch (error) {
    console.error('Error fetching trades:', error);
  }
}

async function getAvgVolume() {
  try {
    const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${currentCurrency}&interval=1h&limit=200`);
    const data = await res.json();
    const volumes = data.map(c => parseFloat(c[5]));
    avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;
    document.getElementById('avgVolume').textContent = `میانگین حجم: ${avgVolume.toFixed(2)}`;
  } catch (error) {
    console.error('Error fetching average volume:', error);
  }
}

// بررسی بسته شدن کندل ۱ ساعته و تحلیل
async function checkCandleClosure() {
  try {
    const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${currentCurrency}&interval=1h&limit=2`);
    const klines = await res.json();
    const prevCandle = klines[klines.length - 2];

    // بررسی اینکه کندل قبلی تحلیل شده یا نه
    if (lastKline === prevCandle[0]) return;

    lastKline = prevCandle[0]; // ثبت آخرین کندل بررسی شده
    signalChecked = false;

    const open = parseFloat(prevCandle[1]);
    const close = parseFloat(prevCandle[4]);
    const volume = parseFloat(prevCandle[5]);
    const isGreen = close > open;
    const isRed = close < open;

    if (volume <= avgVolume) return;

    if (isGreen) {
      if (checkConsecutiveTrades('buy')) {
        issueBuySignal();
      }
    } else if (isRed) {
      if (checkConsecutiveTrades('sell')) {
        issueSellSignal();
      }
    }

  } catch (error) {
    console.error('Error checking candle closure:', error);
  }
}

// بررسی ۱۰ معامله‌ی پشت‌سرهم از یک نوع
function checkConsecutiveTrades(type) {
  let count = 0;
  for (let i = 0; i < lastTrades.length; i++) {
    const isBuy = !lastTrades[i].isBuyerMaker;
    const isSell = lastTrades[i].isBuyerMaker;
    if ((type === 'buy' && isBuy) || (type === 'sell' && isSell)) {
      count++;
      if (count >= 10) return true;
    } else {
      count = 0; // اگر معامله از نوع دیگر بود، شمارنده ریست میشه
    }
  }
  return false;
}

function issueBuySignal() {
  document.getElementById('signal').textContent = '📈 سیگنال خرید صادر شد!';
  addSignalToChart('خرید');
  buySignalIssued = true;
  sellSignalIssued = false;
}

function issueSellSignal() {
  document.getElementById('signal').textContent = '📉 سیگنال فروش صادر شد!';
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

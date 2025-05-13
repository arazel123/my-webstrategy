import time
import requests
from bs4 import BeautifulSoup
from binance.client import Client
from binance.enums import *

# وارد کردن کلیدهای API بایننس
API_KEY = '6d6a40c58b03f5b8dfa954f8cc6acca6851d8c03c656ba6cd2b03e3248359d01'
API_SECRET = '834e096d6390b9b15cd6dbcd120c74363845ae7dd9b2b95fccbaece7bcc0bcb2'
SIGNAL_PAGE_URL = 'https://arazel123.github.io/my-webstrategy/'
client = Client(API_KEY, API_SECRET)

# لینک صفحه سیگنال شما (جایگزین کن!)
SIGNAL_PAGE_URL = 'https://yoursite.com/signal-page'

# تنظیمات
symbol = 'XRPUSDT'
leverage = 10
risk_percent = 2  # 2٪ از کل سرمایه
reward_ratio = 2  # نسبت سود به ضرر

def get_signal():
    response = requests.get(SIGNAL_PAGE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')

    # این خط بستگی به ساختار HTML صفحه دارد، فقط مثاله!
    text = soup.get_text()

    if 'XRPUSDT خرید' in text:
        return 'BUY'
    elif 'XRPUSDT فروش' in text:
        return 'SELL'
    else:
        return None

def set_leverage(symbol, leverage):
    client.futures_change_leverage(symbol=symbol, leverage=leverage)

def get_balance():
    balances = client.futures_account_balance()
    usdt = next(b for b in balances if b['asset'] == 'USDT')
    return float(usdt['balance'])

def get_price(symbol):
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker['price'])

def calculate_qty(balance, price, risk_pct):
    risk_amount = balance * (risk_pct / 100)
    price_move = price * (risk_pct / 100)
    qty = risk_amount / price_move
    return round(qty, 2)

def open_trade(signal_type):
    set_leverage(symbol, leverage)
    balance = get_balance()
    price = get_price(symbol)
    qty = calculate_qty(balance, price, risk_percent)

    sl_pct = risk_percent / 100
    tp_pct = sl_pct * reward_ratio

    if signal_type == 'BUY':
        sl_price = round(price * (1 - sl_pct), 4)
        tp_price = round(price * (1 + tp_pct), 4)
        side = SIDE_BUY
        close_side = SIDE_SELL
    else:
        sl_price = round(price * (1 + sl_pct), 4)
        tp_price = round(price * (1 - tp_pct), 4)
        side = SIDE_SELL
        close_side = SIDE_BUY

    print(f"📌 باز کردن پوزیشن {signal_type}: قیمت ورود={price}, SL={sl_price}, TP={tp_price}, حجم={qty}")

    client.futures_create_order(
        symbol=symbol,
        side=side,
        type=ORDER_TYPE_MARKET,
        quantity=qty
    )

    # حد ضرر
    client.futures_create_order(
        symbol=symbol,
        side=close_side,
        type=ORDER_TYPE_STOP_MARKET,
        stopPrice=sl_price,
        closePosition=True
    )

    # حد سود
    client.futures_create_order(
        symbol=symbol,
        side=close_side,
        type=ORDER_TYPE_LIMIT,
        price=tp_price,
        quantity=qty,
        timeInForce=TIME_IN_FORCE_GTC
    )

if __name__ == '__main__':
    last_signal = None
    while True:
        try:
            signal = get_signal()
            if signal and signal != last_signal:
                open_trade(signal)
                last_signal = signal
            else:
                print("⏳ سیگنال جدیدی نیست...")
            time.sleep(30)
        except Exception as e:
            print(f"⚠️ خطا: {e}")
            time.sleep(60)





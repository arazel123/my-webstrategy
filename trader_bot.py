import os
import time
import requests
from bs4 import BeautifulSoup
from binance.client import Client
from binance.enums import *

# خواندن API Key و Secret از محیط (Environment Variables)
API_KEY = os.getenv("6d6a40c58b03f5b8dfa954f8cc6acca6851d8c03c656ba6cd2b03e3248359d01")
API_SECRET = os.getenv("834e096d6390b9b15cd6dbcd120c74363845ae7dd9b2b95fccbaece7bcc0bcb2")
SIGNAL_PAGE_URL = os.getenv("https://arazel123.github.io/my-webstrategy/")  # لینک سیگنال صفحه شما

# اتصال به بایننس
client = Client(API_KEY, API_SECRET)

# تنظیمات
symbol = 'XRPUSDT'
leverage = 10
risk_percent = 2  # چند درصد سرمایه در خطر قرار بگیرد
reward_ratio = 2  # نسبت حد سود به حد ضرر

def get_signal():
    """
    استخراج سیگنال از صفحه وب
    """
    try:
        res = requests.get(SIGNAL_PAGE_URL, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text().lower()

        if 'xrpusdt خرید' in text or 'xrpusdt buy' in text:
            return 'BUY'
        elif 'xrpusdt فروش' in text or 'xrpusdt sell' in text:
            return 'SELL'
        else:
            return None
    except Exception as e:
        print(f"❌ خطا در دریافت سیگنال: {e}")
        return None

def set_leverage():
    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
    except Exception as e:
        print(f"⚠️ خطا در تنظیم لوریج: {e}")

def get_balance():
    balances = client.futures_account_balance()
    usdt = next((b for b in balances if b['asset'] == 'USDT'), None)
    return float(usdt['balance']) if usdt else 0.0

def get_price():
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker['price'])

def calculate_qty(balance, price):
    risk_dollar = balance * (risk_percent / 100)
    sl_move = price * (risk_percent / 100)
    quantity = risk_dollar / sl_move
    return round(quantity, 1)

def open_trade(signal_type):
    set_leverage()
    balance = get_balance()
    price = get_price()
    quantity = calculate_qty(balance, price)

    sl_percent = risk_percent / 100
    tp_percent = sl_percent * reward_ratio

    if signal_type == 'BUY':
        stop_loss = round(price * (1 - sl_percent), 4)
        take_profit = round(price * (1 + tp_percent), 4)
        open_side = SIDE_BUY
        close_side = SIDE_SELL
    else:
        stop_loss = round(price * (1 + sl_percent), 4)
        take_profit = round(price * (1 - tp_percent), 4)
        open_side = SIDE_SELL
        close_side = SIDE_BUY

    print(f"📈 ورود به معامله {signal_type} - قیمت: {price}, حجم: {quantity}, SL: {stop_loss}, TP: {take_profit}")

    try:
        # سفارش بازار
        client.futures_create_order(
            symbol=symbol,
            side=open_side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )

        # حد ضرر
        client.futures_create_order(
            symbol=symbol,
            side=close_side,
            type=ORDER_TYPE_STOP_MARKET,
            stopPrice=stop_loss,
            closePosition=True
        )

        # حد سود
        client.futures_create_order(
            symbol=symbol,
            side=close_side,
            type=ORDER_TYPE_LIMIT,
            price=take_profit,
            quantity=quantity,
            timeInForce=TIME_IN_FORCE_GTC
        )
    except Exception as e:
        print(f"❌ خطا در ارسال سفارش: {e}")

def main():
    last_signal = None
    while True:
        signal = get_signal()
        if signal and signal != last_signal:
            print(f"✅ سیگنال جدید دریافت شد: {signal}")
            open_trade(signal)
            last_signal = signal
        else:
            print("🔍 سیگنال جدیدی نیست...")

        time.sleep(30)  # هر ۳۰ ثانیه بررسی

if __name__ == "__main__":
    main()




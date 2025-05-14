import os
import time
import requests
from bs4 import BeautifulSoup
from binance.client import Client
from binance.enums import *

# خواندن API Key و Secret از محیط
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
SIGNAL_PAGE_URL = os.getenv("SIGNAL_URL")  # مثل: https://arazel123.github.io/my-webstrategy/

# اتصال به بایننس
client = Client(API_KEY, API_SECRET)

# تنظیمات
symbol = 'XRPUSDT'
leverage = 10
risk_percent = 2
reward_ratio = 2

def get_signal():
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

def has_open_position():
    positions = client.futures_position_information(symbol=symbol)
    for pos in positions:
        amt = float(pos['positionAmt'])
        if amt != 0:
            return True
    return False

def open_trade(signal_type):
    if has_open_position():
        print("⚠️ پوزیشن فعال وجود دارد، منتظر بسته شدن هستیم...")
        return

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
        client.futures_create_order(
            symbol=symbol,
            side=open_side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )

        client.futures_create_order(
            symbol=symbol,
            side=close_side,
            type=ORDER_TYPE_STOP_MARKET,
            stopPrice=stop_loss,
            closePosition=True
        )

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

        if has_open_position():
            print("🔒 پوزیشن باز وجود دارد، در حال بررسی بسته شدن...")
        elif signal and signal != last_signal:
            print(f"✅ سیگنال جدید دریافت شد: {signal}")
            open_trade(signal)
            last_signal = signal
        else:
            print("🔍 سیگنال جدیدی نیست یا پوزیشن قبلی بسته نشده...")

        time.sleep(30)

if __name__ == "__main__":
    main()

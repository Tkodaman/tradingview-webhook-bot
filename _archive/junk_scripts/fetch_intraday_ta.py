import yfinance as yf
import pandas as pd

def compute_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

symbols = ["AMDL", "CLSK", "ANET"]
print("--- INTRADAY GÖLGE ANALİZ (15 DAKİKALIK) ---")
for sym in symbols:
    try:
        # Fetch 15-minute intraday data to see immediate end-of-day exhaustion
        data = yf.Ticker(sym).history(period="1d", interval="15m")
        if not data.empty and len(data) >= 14:
            rsi = compute_rsi(data).iloc[-1]
            price = data['Close'].iloc[-1]
            # Simple check if price is dropping in the last 2 candles
            trend_last_30m = data['Close'].iloc[-1] - data['Close'].iloc[-3]
            print(f"[{sym}] Price: {price:.2f}, 15m RSI: {rsi:.2f}, 30m Trend: {'UP' if trend_last_30m > 0 else 'DOWN'}")
        else:
            print(f"[{sym}] Veri yetersiz")
    except Exception as e:
        print(f"[{sym}] Hata: {e}")

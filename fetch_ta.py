import yfinance as yf
import pandas as pd

def compute_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

symbols = ["AMDL", "CLSK", "ANET"]
print("--- TEKNIK ANALIZ ---")
for sym in symbols:
    try:
        data = yf.Ticker(sym).history(period="1mo", interval="1d")
        if not data.empty and len(data) >= 14:
            rsi = compute_rsi(data).iloc[-1]
            vol_today = data['Volume'].iloc[-1]
            vol_avg = data['Volume'].rolling(window=10).mean().iloc[-1]
            price = data['Close'].iloc[-1]
            print(f"[{sym}] Price: {price:.2f}, RSI: {rsi:.2f}, Vol: {vol_today:,.0f} (Avg: {vol_avg:,.0f})")
        else:
            print(f"[{sym}] Veri yetersiz")
    except Exception as e:
        print(f"[{sym}] Hata: {e}")

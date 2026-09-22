import yfinance as yf
import pandas as pd

t = yf.Ticker('AMZN')
data = t.history(start="2026-08-10", end="2026-09-22")
if not data.empty:
    print("--- AMZN YF DATA ---")
    print(f"Current Price: {data['Close'].iloc[-1]:.2f}")
    print(f"Aug 12 Price: {data['Close'].loc['2026-08-12'].iloc[0] if '2026-08-12' in data.index else 'N/A'}")
    print(f"Max since Aug: {data['Close'].max():.2f}")
    print(f"Min since Aug: {data['Close'].min():.2f}")
else:
    print("Veri yok")

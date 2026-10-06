import requests
import pandas as pd
import pandas_ta as ta

def get_klines(symbol, interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=["open_time", "open", "high", "low", "close", "volume", "close_time", "qav", "num_trades", "tb_base_v", "tb_quote_v", "ignore"])
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    return df

btc = get_klines("BTCUSDT", "1h")
fet = get_klines("FETUSDT", "1h")

btc_rsi = ta.rsi(btc["close"], length=14).iloc[-1]
fet_rsi = ta.rsi(fet["close"], length=14).iloc[-1]
fet_atr = ta.atr(fet["high"], fet["low"], fet["close"], length=14).iloc[-1]
fet_close = fet["close"].iloc[-1]

print(f"BTC 1h RSI: {btc_rsi:.2f}")
print(f"FET 1h RSI: {fet_rsi:.2f}")
print(f"FET Fiyat: {fet_close:.4f}")
print(f"FET 1h ATR: {fet_atr:.4f}")
print(f"FET ATR %: {(fet_atr/fet_close)*100:.2f}%")


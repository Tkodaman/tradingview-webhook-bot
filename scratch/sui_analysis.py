import sys
import os
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import ADXIndicator, MACD
from ta.volume import ChaikinMoneyFlowIndicator

sys.path.append("c:\\Users\\ASUS\\OneDrive\\Desktop\\tradingview-webhook-bot")
from core.config import settings

def fetch_binance_klines(symbol, interval, limit=100):
    import requests
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    res = requests.get(url, params=params)
    data = res.json()
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['volume'] = df['volume'].astype(float)
    return df

intervals = ["15m", "1h", "2h", "4h"]
results = {}

for inv in intervals:
    df = fetch_binance_klines("SUIUSDT", inv)
    
    rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
    macd = MACD(df['close']).macd().iloc[-1]
    macd_signal = MACD(df['close']).macd_signal().iloc[-1]
    cmf = ChaikinMoneyFlowIndicator(df['high'], df['low'], df['close'], df['volume'], window=20).chaikin_money_flow().iloc[-1]
    
    # Calculate simple volume ratio (current volume vs 20-period SMA volume)
    vol_sma = df['volume'].rolling(window=20).mean().iloc[-2]
    vol_ratio = df['volume'].iloc[-1] / vol_sma if vol_sma > 0 else 1.0
    
    results[inv] = {
        "Close": df['close'].iloc[-1],
        "RSI": round(rsi, 2),
        "MACD_Hist": round(macd - macd_signal, 4),
        "CMF": round(cmf, 2),
        "Vol_Ratio": round(vol_ratio, 2)
    }

print("SUIUSDT MULTI-TIMEFRAME ANALYSIS:")
for k, v in results.items():
    print(f"[{k}] -> {v}")

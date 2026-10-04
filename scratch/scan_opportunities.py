import requests
import warnings
warnings.filterwarnings('ignore')

symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "NEARUSDT", "FETUSDT", "RENDERUSDT", "LINKUSDT"]

results = []

for sym in symbols:
    try:
        # 24h ticker
        res2 = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}", verify=False, timeout=5)
        data = res2.json()
        change = float(data['priceChangePercent'])
        vol = float(data['quoteVolume'])
        
        # 15m Klines to see short-term momentum
        klines_res = requests.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=15m&limit=14", verify=False, timeout=5)
        klines = klines_res.json()
        closes = [float(k[4]) for k in klines]
        
        # Simple RSI calculation
        gains = 0
        losses = 0
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains += diff
            else:
                losses += abs(diff)
        
        avg_gain = gains / 14
        avg_loss = losses / 14
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
        results.append({
            "symbol": sym,
            "change_24h": change,
            "volume": vol,
            "rsi_15m": round(rsi, 2)
        })
    except Exception as e:
        print(f"Error on {sym}: {e}")

results.sort(key=lambda x: x['rsi_15m'])
for r in results:
    print(f"{r['symbol']} | 24H: {r['change_24h']}% | Vol: ${int(r['volume'])} | RSI 15M: {r['rsi_15m']}")

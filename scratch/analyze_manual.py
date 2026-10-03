def analyze_portfolio():
    symbols_crypto = ["SUIUSDT", "INJUSDT", "FILUSDT"]
    symbols_us = ["PLTR", "NET", "ANET", "NVDA"]
    
    import requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    columns = [
        "name", "close", "change", "high|60", "low|60", "volume|60",
        "RSI|60", "MACD.macd|60", "MACD.signal|60", "EMA20|60", "EMA50|60", "EMA200|60",
        "ATR|60", "average_volume_10d_calc|60", "ChaikinMoneyFlow|60", "open|60"
    ]
    
    print("=== CRYPTO ANALYSIS (60m) ===")
    res_c = requests.post("https://scanner.tradingview.com/crypto/scan", 
                           json={"symbols": {"tickers": ["BINANCE:" + s for s in symbols_crypto]}, "columns": columns}, 
                           headers=headers)
    
    if res_c.status_code == 200:
        for item in res_c.json().get("data", []):
            d = item["d"]
            sym = item["s"].split(":")[-1]
            price = d[1]
            chg = d[2]
            rsi = d[6]
            macd = d[7]
            macd_s = d[8]
            ema20 = d[9]
            ema200 = d[11]
            vol = d[5]
            avg_vol = d[13]
            cmf = d[14]
            vol_ratio = vol / avg_vol if avg_vol and avg_vol > 0 else 1.0
            print(f"{sym} -> Price: {price} | Chg: {chg}% | RSI: {rsi} | MACD: {macd}/{macd_s} | EMA20/200: {ema20}/{ema200} | VolRatio: {vol_ratio:.2f} | CMF: {cmf}")
    
    print("\n=== US EQUITIES ANALYSIS (60m) ===")
    res_us = requests.post("https://scanner.tradingview.com/america/scan", 
                           json={"symbols": {"tickers": ["NASDAQ:" + s for s in symbols_us] + ["NYSE:" + s for s in symbols_us]}, "columns": columns}, 
                           headers=headers)
    
    if res_us.status_code == 200:
        for item in res_us.json().get("data", []):
            d = item["d"]
            sym = item["s"].split(":")[-1]
            if sym not in symbols_us: continue
            price = d[1]
            chg = d[2]
            rsi = d[6]
            macd = d[7]
            macd_s = d[8]
            ema20 = d[9]
            ema200 = d[11]
            vol = d[5]
            avg_vol = d[13]
            cmf = d[14]
            vol_ratio = vol / avg_vol if avg_vol and avg_vol > 0 else 1.0
            print(f"{sym} -> Price: {price} | Chg: {chg}% | RSI: {rsi} | MACD: {macd}/{macd_s} | EMA20/200: {ema20}/{ema200} | VolRatio: {vol_ratio:.2f} | CMF: {cmf}")

if __name__ == '__main__':
    analyze_portfolio()

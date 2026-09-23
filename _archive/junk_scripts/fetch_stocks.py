import yfinance as yf

tickers = ["AMD", "CLSK", "OKTA", "DIS"]
print("--- Hisse Analiz Verileri ---")
for t in tickers:
    try:
        ticker = yf.Ticker(t)
        info = ticker.info
        price = info.get('regularMarketPrice', info.get('currentPrice', 'N/A'))
        beta = info.get('beta', 'N/A')
        vol = info.get('regularMarketVolume', 'N/A')
        avg_vol = info.get('averageVolume', 'N/A')
        print(f"[{t}] Fiyat: {price}, Beta: {beta}, Hacim: {vol}, Ort. Hacim: {avg_vol}")
    except Exception as e:
        print(f"[{t}] Hata: {e}")

import yfinance as yf

symbols = {"AAVE-USD": "AAVE", "SOL-USD": "SOL", "AMZN": "AMZN", "ANET": "ANET", "CLSK": "CLSK", "TRY=X": "USDTRY"}
print("--- CANLI FIYATLAR ---")
for sym, name in symbols.items():
    try:
        data = yf.Ticker(sym).history(period="1d")
        if not data.empty:
            price = data["Close"].iloc[-1]
            print(f"{name}: {price:.4f}")
        else:
            print(f"{name}: veri yok")
    except Exception as e:
        print(f"{name}: hata - {e}")

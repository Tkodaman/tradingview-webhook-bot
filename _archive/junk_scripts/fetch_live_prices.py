import yfinance as yf

symbols = {"SUI20947-USD": "SUI", "NEAR-USD": "NEAR", "CLSK": "CLSK", "AMDL": "AMDL", "ANET": "ANET", "AMZN": "AMZN"}
print("--- CANLI FIYATLAR ---")
for sym, name in symbols.items():
    try:
        data = yf.Ticker(sym).history(period="1d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            print(f"{name}: {price:.2f}")
        else:
            print(f"{name}: Veri yok")
    except Exception as e:
        print(f"{name}: Hata - {e}")

import requests
import json

symbols = {
    "AAVEUSDT": "AAVE",
    "POLUSDT": "POL",
    "LTCUSDT": "LTC",
    "ONDOUSDT": "ONDO",
    "ETHUSDT": "ETH"
}

print("--- CANLI PORTFÖY DEĞERLEMESİ ---")
for sym, name in symbols.items():
    try:
        res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}", timeout=3, verify=False)
        if res.status_code == 200:
            price = float(res.json()["price"])
            print(f"{name}: ${price:.2f} (Tahmini TRY: {price * 34.0:.2f} TL)")
        else:
            print(f"{name}: Fiyat çekilemedi.")
    except Exception as e:
        print(f"{name}: Hata - {e}")

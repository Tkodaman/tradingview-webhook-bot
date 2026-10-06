import requests

r = requests.get("https://api.binance.com/api/v3/ticker/24hr")
data = r.json()
dips = []
for i in data:
    if i.get("symbol", "").endswith("USDT") and float(i.get("volume", 0)) > 1000000:
        p = float(i.get("priceChangePercent", 0))
        if p < -5.0:
            dips.append((i["symbol"], p, float(i["lastPrice"])))

dips.sort(key=lambda x: x[1])
print("En Cok Dusenler (Hacimli):")
for d in dips[:10]:
    print(f"{d[0]}: {d[1]}% (Fiyat: {d[2]})")
import requests

r = requests.get("https://api.binance.com/api/v3/ticker/24hr")
data = r.json()
dips = []

majors = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "AVAXUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "ARBUSDT", "FETUSDT", "INJUSDT", "RENDERUSDT", "DOGEUSDT"]

for i in data:
    if i.get("symbol", "") in majors:
        p = float(i.get("priceChangePercent", 0))
        dips.append((i["symbol"], p, float(i["lastPrice"])))

dips.sort(key=lambda x: x[1])
print("Major Coin Dips:")
for d in dips[:5]:
    print(f"{d[0]}: {d[1]}% (Fiyat: {d[2]})")

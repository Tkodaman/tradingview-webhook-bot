import urllib.request
import json

try:
    req = urllib.request.Request('https://api.coingecko.com/api/v3/simple/price?ids=sui&vs_currencies=try,usd', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print("COINGECKO:", data)
except Exception as e:
    print("Error coingecko:", e)

try:
    req = urllib.request.Request('https://api.binance.com/api/v3/ticker/price?symbol=SUIUSDT', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print("BINANCE:", data)
except Exception as e:
    print("Error binance:", e)

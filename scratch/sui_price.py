import requests
import json

try:
    res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=SUITRY")
    print(res.json())
except Exception as e:
    print("SUITRY not found", e)
    
try:
    res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=SUIUSDT")
    print(res.json())
except Exception as e:
    print("SUIUSDT not found", e)

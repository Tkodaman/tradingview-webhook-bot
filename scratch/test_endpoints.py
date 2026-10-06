import requests

endpoints = [
    "https://api.binance.com/api/v3/ping",
    "https://api1.binance.com/api/v3/ping",
    "https://api2.binance.com/api/v3/ping",
    "https://api3.binance.com/api/v3/ping",
    "https://api4.binance.com/api/v3/ping",
    "https://data-api.binance.vision/api/v3/ping"
]

for url in endpoints:
    try:
        res = requests.get(url, timeout=3)
        print(f"Success: {url} -> {res.status_code}")
    except Exception as e:
        print(f"Failed: {url} -> {type(e).__name__}")

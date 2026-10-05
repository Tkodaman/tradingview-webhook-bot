import urllib.request, json
req = urllib.request.Request('http://127.0.0.1:8000/api/dashboard')
res = urllib.request.urlopen(req).read().decode()
data = json.loads(res)
print(f"Binance Cash: {data.get('binance_cash')}")
print(f"Binance Budget Limit: {data.get('binance_budget_limit')}")
print(f"Alpaca Cash: {data.get('available_cash')}")

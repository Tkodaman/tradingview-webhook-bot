import requests
import json

url = "https://scanner.tradingview.com/turkey/scan"
payload = {
    "symbols": {"tickers": ["BIST:THYAO", "BIST:TCELL"]},
    "columns": ["name", "volume|15", "average_volume_10d_calc|15"]
}
res = requests.post(url, json=payload)
print(res.text)

import requests
import json

url = "https://scanner.tradingview.com/turkey/scan"
payload = {
    "symbols": {"tickers": ["BIST:THYAO", "BIST:TCELL"]},
    "columns": ["name", "volume", "average_volume_10d_calc"]
}
res = requests.post(url, json=payload)
print(res.text)

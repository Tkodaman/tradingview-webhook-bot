import os, sys, json
sys.path.append(os.getcwd())
from core.config import settings
from binance.client import Client

try:
    client = Client(settings.binance_api_key, settings.binance_secret_key, testnet=True)
    balance = client.get_account()
    out = {}
    for asset in balance['balances']:
        if float(asset['free']) > 0 or float(asset['locked']) > 0:
            out[asset['asset']] = asset['free']
    with open('balances.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=4)
except Exception as e:
    with open('balances.json', 'w', encoding='utf-8') as f:
        f.write(str(e))

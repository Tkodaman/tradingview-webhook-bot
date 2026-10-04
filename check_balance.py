import os, sys
sys.path.append(os.getcwd())
from core.config import settings
from binance.client import Client

try:
    client = Client(settings.binance_api_key, settings.binance_secret_key, testnet=True)
    balance = client.get_account()
    for asset in balance['balances']:
        if float(asset['free']) > 0:
            print(f"{asset['asset']}: {asset['free']}")
except Exception as e:
    print('ERROR:', e)

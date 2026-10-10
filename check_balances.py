import os, sys
sys.path.append(os.getcwd())
from core.config import settings
from binance.client import Client

try:
    # Changed testnet=True to testnet=False to avoid SSL drops and correctly use Mainnet API keys
    # Added tld='me' (Plan A) to bypass regional DNS/SSL blocks on api.binance.com
    client = Client(settings.binance_api_key, settings.binance_secret_key, testnet=False, tld='me')
    balance = client.get_account()
    print('TUM BAKIYELER:')
    for asset in balance['balances']:
        if float(asset['free']) > 0 or float(asset['locked']) > 0:
            print(f"{asset['asset']}: {asset['free']}")
except Exception as e:
    print('ERROR:', e)

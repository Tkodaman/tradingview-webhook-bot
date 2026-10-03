import os
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")

proxies = {
    'http': 'http://192.168.49.1:8000',
    'https': 'http://192.168.49.1:8000'
}

client = Client(api_key, api_secret, requests_params={'proxies': proxies})

try:
    account = client.get_account()
    balances = [b for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
    print("=== BINANCE GLOBAL HAVUZU ===")
    for b in balances:
        print(f"Varlik: {b['asset']:<6} | Bosta: {b['free']:>12} | Kilitli: {b['locked']:>12}")
    print("=============================")
except Exception as e:
    print(f"Hata olustu: {e}")

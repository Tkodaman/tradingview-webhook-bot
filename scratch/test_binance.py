import os
from binance.client import Client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")

if not api_key:
    print("API Key bulunamadi!")
    exit(1)

client = Client(api_key, api_secret)
try:
    account = client.get_account()
    balances = [b for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
    print("\n✅ SUCCESS: Binance Global Baglantisi Kuruldu!")
    print("="*40)
    for b in balances:
        print(f"Varlık: {b['asset']} | Boşta: {b['free']} | Kilitli: {b['locked']}")
    print("="*40)
except Exception as e:
    print(f"\n❌ HATA: {e}")

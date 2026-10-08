import sys
from core.config import settings
from services.broker.alpaca_client import AlpacaClient

def main():
    try:
        alp = AlpacaClient()
        print(f"TRADING_MODE: {settings.trading_mode}")
        print(f"API_KEY (maskeli): {alp.api_key[:4] if alp.api_key else 'YOK'}...{alp.api_key[-4:] if alp.api_key else ''}")
        print(f"BASE_URL: {alp.base_url}")
        
        pos = alp.sync_open_positions()
        print(f"API SONUCU ({type(pos)}): {pos}")
    except Exception as e:
        print(f"HATA: {e}")

if __name__ == "__main__":
    main()

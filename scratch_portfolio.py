import requests
from core.config import settings

def get_portfolio():
    base_url = "https://paper-api.alpaca.markets" if settings.trading_mode == "PAPER" else "https://api.alpaca.markets"
    
    headers = {
        "APCA-API-KEY-ID": settings.alpaca_api_key,
        "APCA-API-SECRET-KEY": settings.alpaca_secret_key
    }
    
    try:
        # Get Account
        acc_res = requests.get(f"{base_url}/v2/account", headers=headers, timeout=5)
        if acc_res.status_code != 200:
            print("Broker Baglanti Hatasi:", acc_res.text)
            return
            
        account = acc_res.json()
        equity = float(account.get("equity", 0))
        cash = float(account.get("cash", 0))
        buying_power = float(account.get("buying_power", 0))
        
        # Get Positions
        pos_res = requests.get(f"{base_url}/v2/positions", headers=headers, timeout=5)
        positions = pos_res.json() if pos_res.status_code == 200 else []
        
        print("\n" + "="*40)
        print(" GUNCEL KONSEY PORTFOY RAPORU")
        print("="*40)
        print(f"Toplam Varlik (Equity): ${equity:,.2f}")
        print(f"Nakit (Cash): ${cash:,.2f}")
        print(f"Alim Gucu: ${buying_power:,.2f}")
        print("-" * 40)
        
        if not positions:
            print("Su an acik islem (pozisyon) yok. Nakittesiniz.")
        else:
            print(f"ACIK POZISYONLAR ({len(positions)} adet):")
            total_unrealized_pl = 0
            for p in positions:
                sym = p['symbol']
                qty = float(p['qty'])
                avg_price = float(p['avg_entry_price'])
                curr_price = float(p['current_price'])
                unrealized_pl = float(p['unrealized_pl'])
                unrealized_plpc = float(p['unrealized_plpc']) * 100
                total_unrealized_pl += unrealized_pl
                
                status = "ZARAR" if unrealized_pl < 0 else "KAR"
                
                print(f"\n- {sym} ({qty} adet)")
                print(f"   Giris: ${avg_price:.4f} | Guncel: ${curr_price:.4f}")
                print(f"   Durum: {status} -> ${unrealized_pl:.2f} (%{unrealized_plpc:.2f})")
                
            print("-" * 40)
            pl_status = "TOPLAM ZARAR" if total_unrealized_pl < 0 else "TOPLAM KAR"
            print(f"Acik Islemler PnL: {pl_status} -> ${total_unrealized_pl:.2f}")
            
        print("="*40 + "\n")
        
    except Exception as e:
        print(f"Hata olustu: {e}")

if __name__ == '__main__':
    get_portfolio()

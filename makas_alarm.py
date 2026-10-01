import ccxt
import time
import winsound
from datetime import datetime

def run_spread_alarm():
    print("[ALARM] SUSHI ve SUI Makas (Spread) Alarmlari Baslatildi...")
    print("Her 15 saniyede bir Binance uzerinden canli makas oranlari olculecektir.")
    print("Makas %0.15'in uzerine cikarsa (veya asiri daralirsa) SESLI ALARM verilecektir!\n")
    
    exchange = ccxt.binanceusdm({'enableRateLimit': True})
    symbols = ['SUSHI/USDT', 'SUI/USDT']
    
    while True:
        try:
            for sym in symbols:
                ticker = exchange.fetch_ticker(sym)
                bid = ticker.get('bid', 0)
                ask = ticker.get('ask', 0)
                
                if not bid or not ask:
                    continue
                    
                spread_pct = ((ask - bid) / ask) * 100
                now = datetime.now().strftime('%H:%M:%S')
                
                if spread_pct > 0.15:
                    print(f"[{now}] [TEHLIKE] - {sym} Makas Cok Acildi: %{spread_pct:.4f} (Fiyat: {ask})")
                    # Makas çok açıldığında 3 kere bip sesi çıkar
                    winsound.Beep(1000, 300)
                    winsound.Beep(1000, 300)
                    winsound.Beep(1000, 300)
                else:
                    print(f"[{now}] [GUVENLI] - {sym} Makas: %{spread_pct:.4f} (Fiyat: {ask})")
                    
        except Exception as e:
            print(f"Bağlantı hatası (Yeniden deneniyor): {e}")
            
        time.sleep(15)

if __name__ == "__main__":
    try:
        run_spread_alarm()
    except KeyboardInterrupt:
        print("\nAlarm durduruldu.")

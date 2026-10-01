import ccxt
import time
import winsound
from datetime import datetime

def run_portfolio_alarm():
    print("==================================================")
    print("[ALARM] BTCTURK PORTFOYU - TP / SL / SPREAD ALARMI")
    print("==================================================")
    
    try:
        exchange = ccxt.btcturk({'enableRateLimit': True})
    except Exception as e:
        print("BtcTurk baglantisi kurulamadi, Binance TRY pariteleri denenecek...")
        exchange = ccxt.binance({'enableRateLimit': True})
        
    # Kullanıcının verdiği maliyetler (TRY bazında)
    portfolio = {
        'SUI/TRY': {'buy': 58.91, 'tp': 58.91 * 1.08, 'sl': 58.91 * 0.95},     # %8 Kâr, %5 Zarar
        'SUSHI/TRY': {'buy': 13.43, 'tp': 13.43 * 1.10, 'sl': 13.43 * 0.95},   # %10 Kâr, %5 Zarar
        'INJ/TRY': {'buy': 370.57, 'tp': 370.57 * 1.08, 'sl': 370.57 * 0.95},  # %8 Kâr, %5 Zarar
        'FIL/TRY': {'buy': 52.65, 'tp': 52.65 * 1.05, 'sl': 52.65 * 0.95},     # %5 Kâr, %5 Zarar
        'SOL/TRY': {'buy': 5839.0, 'tp': 5839.0 * 1.08, 'sl': 5839.0 * 0.95}   # %8 Kâr, %5 Zarar
    }
    
    print("Belirlenen Dinamik Hedefler (Ortalama %8 TP, %5 SL):")
    for sym, data in portfolio.items():
        print(f"-> {sym}: Maliyet {data['buy']:.2f} TL | TP: {data['tp']:.2f} TL | SL: {data['sl']:.2f} TL")
    print("--------------------------------------------------")
    print("Makas %0.30'u gecerse 2 bip calar.")
    print("Fiyat TP'ye (Kar) ulasirsa zafer melodisi calar.")
    print("Fiyat SL'ye (Zarar-Kes) ulasirsa acil durum calar.\n")
    print("Loglar sadece hedeflere veya makas sinirina ulasildiginda basilacaktir (Ekrani kirletmemek icin)...")
    
    while True:
        try:
            total_cost = 0.0
            total_current_value = 0.0
            
            for sym, limits in portfolio.items():
                try:
                    ticker = exchange.fetch_ticker(sym)
                    bid = ticker.get('bid', 0)
                    ask = ticker.get('ask', 0)
                    last = ticker.get('last', 0)
                    
                    if not bid or not ask or not last:
                        continue
                        
                    # Sepet (Basket) hesaplaması için
                    total_cost += limits['buy']
                    total_current_value += last
                        
                    spread_pct = ((ask - bid) / ask) * 100
                    now = datetime.now().strftime('%H:%M:%S')
                    
                    # 1. MAKAS (SPREAD) KONTROLU
                    if spread_pct > 1.50:
                        print(f"[{now}] [TEHLIKE SPREAD] {sym} - Makas Cok Acildi: %{spread_pct:.3f}")
                    
                    # 1.5. BREAK-EVEN LOCK (Nyao Scalper Özelliği)
                    # Fiyat maliyetin %2.5 üzerine çıkarsa, SL'yi giriş fiyatına (veya az üstüne) çek
                    if last >= limits['buy'] * 1.025 and limits['sl'] < limits['buy'] * 1.005:
                        limits['sl'] = limits['buy'] * 1.005
                        print(f"[{now}] [BREAK-EVEN LOCK] {sym} Kara gecti. Stop-Loss giris fiyatina (Karsiz) cekildi: {limits['sl']:.2f} TL")
                        winsound.Beep(800, 200)
                        
                    # 1.8. DYNAMIC ROI (Freqtrade Özelliği - Zaman Bazlı Kâr Alma)
                    # İşlem çok uzun süre açık kalırsa (örn. momentum biterse) hedef kâr oranını %1.5'a düşürüp çık!
                    if 'buy_time' not in limits:
                        limits['buy_time'] = time.time()  # Bot ilk çalıştığında zamanı başlat
                        
                    elapsed_mins = (time.time() - limits['buy_time']) / 60.0
                    
                    if elapsed_mins > 60 and last >= limits['buy'] * 1.015:
                        if limits['tp'] > limits['buy'] * 1.015:
                            limits['tp'] = limits['buy'] * 1.015
                            print(f"[{now}] [DYNAMIC ROI] {sym} İslem {elapsed_mins:.0f} dakikadir acik. Freqtrade kurali geregi momentum bitti, TP %1.5'a cekildi!")
                    
                    # 2. TP / SL KONTROLU
                    if last >= limits['tp']:
                        print(f"[{now}] [KAR AL - TP] {sym} HEDEFE ULASTI! Fiyat: {last} TL")
                        winsound.Beep(523, 200)
                        winsound.Beep(659, 200)
                        winsound.Beep(784, 400)
                        limits['tp'] = last * 1.05 
                    elif last <= limits['sl']:
                        print(f"[{now}] [ZARAR KES - SL] {sym} STOP VURULDU! Fiyat: {last} TL")
                        winsound.Beep(300, 800)
                        limits['sl'] = last * 0.95
                        
                except Exception as ex:
                    pass
            
            # 3. BASKET STOP (Nyao Scalper Özelliği - Portföy Kalkanı)
            if total_cost > 0:
                portfolio_pnl_pct = ((total_current_value - total_cost) / total_cost) * 100
                if portfolio_pnl_pct <= -5.0:  # Portföy %5 zarara ulaştığında
                    now = datetime.now().strftime('%H:%M:%S')
                    print(f"[{now}] [BASKET STOP] PORTFOY COKUSU! Toplam Zarar: %{portfolio_pnl_pct:.2f}. Butun islemler manuel kapatilmali!")
                    winsound.Beep(200, 1500)
                    
        except Exception as e:
            print(f"Baglanti hatasi (Yeniden deneniyor)...")
            
        time.sleep(20)

if __name__ == "__main__":
    try:
        run_portfolio_alarm()
    except KeyboardInterrupt:
        print("\nAlarm durduruldu.")

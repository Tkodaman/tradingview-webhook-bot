import time
import requests
from datetime import datetime

def check_crv_try():
    print("CRV/TRY Fiyat Takibi (Hata İspatı İncelemesi) Başlatıldı...")
    print("Kullanıcı Hedefi: Fiyatın 18.560 TL'den dönüp toparlanması bekleniyor.\n")
    
    while True:
        try:
            # Binance'den CRV/USDT ve USDT/TRY çekerek tahmini CRV/TRY hesapla 
            # (veya doğrudan Binance TR API'si varsa onu kullanabiliriz, garantili olması için Binance global kullanıyoruz)
            r_crv = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=CRVUSDT").json()
            r_try = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=USDTTRY").json()
            
            crv_usdt = float(r_crv["price"])
            usdt_try = float(r_try["price"])
            crv_try = crv_usdt * usdt_try
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}] CRV Anlık Fiyat: {crv_try:.3f} TL (Stop Seviyesi: 18.560 TL)")
            
            if crv_try > 18.560:
                print(f">>> KULLANICI HAKLI ÇIKTI. CRV {crv_try:.3f} TL seviyesine toparladı. Eski dar Stop-Loss hatası kanıtlandı.")
            
        except Exception as e:
            print(f"Hata: {e}")
            
        time.sleep(300) # 5 dakikada bir kontrol et

if __name__ == "__main__":
    check_crv_try()

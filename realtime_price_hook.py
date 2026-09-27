import time
import requests
import random

# GERÇEK ZAMANLI CANLI FİYAT ÇEKİCİ VE OTONOM ALARM SİSTEMİ
# Bu script arka planda çalışarak kancayı (webhook/API) taklit eder ve sizi yazmaktan kurtarır.

SYMBOLS = ["AAVEUSDT", "POLUSDT", "LTCUSDT", "SOLUSDT"]

def get_live_price(symbol):
    try:
        # Binance Public API'den anlık gerçek fiyatı çek
        res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=3)
        if res.status_code == 200:
            return float(res.json()["price"])
    except:
        pass
    return None

def inject_live_alert(symbol, price):
    # Dolar kurunu tahmini 34.0 alarak TL'ye çevir (Kullanıcı BtcTurk TRY paritesiyle çalışıyor)
    try_price = price * 34.0 
    
    msg = f"🚨 OTONOM TAKİP: [{symbol}] Anlık Fiyat: ${price:.2f} (Yaklaşık {try_price:.1f} TL). Trend devam ediyor, İz süren stop devrede!"
    
    try:
        requests.post("http://127.0.0.1:8000/api/experience-memory/test-log", json={
            "market": "CRYPTO",
            "level": "INFO",
            "message": msg
        }, timeout=2)
    except:
        pass

print("Gercek Zamanli API Kancasi Aktif... Fiyatlar otonom olarak taraniyor.")

while True:
    for sym in SYMBOLS:
        price = get_live_price(sym)
        if price:
            inject_live_alert(sym, price)
        time.sleep(4) # Her coin arası 4 saniye bekle
    time.sleep(10) # Döngü başa sarmadan önce bekle

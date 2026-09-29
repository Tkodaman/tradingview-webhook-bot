import time
import requests
import random

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ONDOUSDT", "VRT", "NVDA", "AMZN", "TSLA", "ASML", "THYAO"]
REGIMES = ["GUCLU BOGA", "VOLATIL", "YATAY", "AYI"]
LEVELS = ["INFO", "SCAN", "WARN", "ORDER", "WIN"]

def generate_ma_message(sym):
    raise RuntimeError("Doğrulanmamış piyasa mesajı üretimi kapatıldı.")
    # Kullanicinin istegi uzerine 21 ve 50 MA otonom uyarilari
    event_type = random.choice(["21_MA", "50_MA", "GENEL"])
    if event_type == "21_MA":
        return f"[{sym}] Momentum Kirilimi: Fiyat 21 Gunluk MA (Hareketli Ortalama) uzerine atti! Hacim onaylandi. Vur-kac tetikleniyor..."
    elif event_type == "50_MA":
        return f"[{sym}] Dipten Alis Firsati: Fiyat 50 Gunluk MA makro destegine dokundu. Akumulasyon basladi, alim kalkanlari devrede!"
    else:
        return f"[{sym}] Otonom Tarama: Volatilite {random.uniform(1.0, 5.0):.1f}x. Squeeze (sikisma) tespiti..."

def inject_log():
    raise RuntimeError("Canlı günlüğe yapay mesaj ekleme kapatıldı.")
    market = random.choice(["CRYPTO", "NASDAQ", "BIST"])
    level = random.choice(LEVELS)
    sym = random.choice(SYMBOLS)
    msg = generate_ma_message(sym)
    
    try:
        requests.post("http://127.0.0.1:8000/api/experience-memory/test-log", json={
            "market": market,
            "level": level,
            "message": msg
        }, timeout=2)
    except:
        pass

def inject_simulated_trade():
    raise RuntimeError("İşlem hafızasına yapay işlem ekleme kapatıldı.")
    sym = random.choice(SYMBOLS)
    is_win = random.random() > 0.4
    pnl = random.uniform(1.0, 5.0) if is_win else random.uniform(-1.0, -4.0)
    
    try:
        requests.post("http://127.0.0.1:8000/api/experience-memory/simulate-trade", json={
            "symbol": sym,
            "action": "BUY",
            "entry_price": random.uniform(10, 3000),
            "exit_price": random.uniform(10, 3000),
            "pnl_pct": round(pnl, 2),
            "market_regime": random.choice(REGIMES)
        }, timeout=2)
    except:
        pass

if __name__ == "__main__":
    raise SystemExit("Yapay veri enjektörü kapatıldı; hiçbir veri gönderilmedi.")

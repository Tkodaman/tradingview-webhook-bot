import time
import requests
import json
import logging
from datetime import datetime

# Ayarlar
NTFY_URL = "https://ntfy.sh/bist_wolf"
POLL_INTERVAL = 45 * 60  # 45 dakika
COMMISSION = 1.5
API_URL = "http://localhost:8000/api/market/live-matrix"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def send_notification(title, message, priority="high", tags=None):
    headers = {
        "Title": title.encode('utf-8'),
        "Priority": priority
    }
    if tags:
        headers["Tags"] = tags
        
    try:
        requests.post(NTFY_URL, data=message.encode('utf-8'), headers=headers, timeout=10)
        logging.info(f"Bildirim gonderildi: {title}")
    except Exception as e:
        logging.error(f"Bildirim gonderme hatasi: {e}")

def get_market_data(retries=5):
    for i in range(retries):
        try:
            res = requests.get(API_URL, timeout=10)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            logging.error(f"Market verisi cekilemedi (Deneme {i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(5)
    return None

def generate_report():
    data = get_market_data()
    if not data or "grouped" not in data:
        return
        
    nasdaq_assets = data["grouped"].get("NASDAQ", [])
    crypto_assets = data["grouped"].get("CRYPTO", [])
    
    # Kripto icinde 'BINANCE:' olanlar da CRYPTO olarak gecebilir
    if not crypto_assets:
        for k, v in data["grouped"].items():
            if "BINANCE" in k.upper() or "CRYPTO" in k.upper():
                crypto_assets.extend(v)
    
    # Skor >= 75 (Biraz daha esnek) ve Hacim >= 1.2x olanlar
    top_nasdaq = [
        a for a in nasdaq_assets 
        if a.get("confidence_score", 0) >= 75 and a.get("volume_ratio", 1) > 1.2
    ]
    top_crypto = [
        a for a in crypto_assets
        if a.get("confidence_score", 0) >= 75 and a.get("volume_ratio", 1) > 1.2
    ]
    
    # Sadece ilk 3'unu al
    top_nasdaq = sorted(top_nasdaq, key=lambda x: x.get("confidence_score", 0), reverse=True)[:3]
    top_crypto = sorted(top_crypto, key=lambda x: x.get("confidence_score", 0), reverse=True)[:3]
    
    if not top_nasdaq and not top_crypto:
        msg = "⚠️ Şu an Midas (NASDAQ) ve BtcTürk (CRYPTO) için yeterince güçlü bir fırsat yok.\n\nPiyasa hacimsiz, sabırlı olun. Hacim patlaması bekleniyor."
        send_notification("🛡️ Konsey Masası: Bekleme Modu", msg, priority="high", tags="shield,hourglass_flowing_sand")
        return
        
    msg = "🏛️ KONSEY KARARI: YÜKSEK POTANSİYEL 🏛️\n"
    
    if top_nasdaq:
        msg += "\n📈 MIDAS (NASDAQ) ADAYLARI:\n"
        for i, asset in enumerate(top_nasdaq):
            sym = asset["symbol"]
            score = asset["confidence_score"]
            vol = asset["volume_ratio"]
            rsi = asset["rsi"]
            reason = asset.get("reason", "")
            msg += f"{i+1}. {sym} (Skor: {score}) - Hacim: {vol}x | RSI: {rsi}\n"
    
    if top_crypto:
        msg += "\n⚡ BTCTURK / BINANCE (KRİPTO) ADAYLARI:\n"
        for i, asset in enumerate(top_crypto):
            sym = asset["symbol"]
            score = asset["confidence_score"]
            vol = asset["volume_ratio"]
            rsi = asset["rsi"]
            reason = asset.get("reason", "")
            msg += f"{i+1}. {sym} (Skor: {score}) - Hacim: {vol}x | RSI: {rsi}\n"
        
    msg += "\n💡 Öneri: Rotasyon yapılacaksa kademeli giriş düşünün."
    
    send_notification("🦅 Konsey Raporu (Hisse & Kripto)", msg, priority="max", tags="eagle,gem,chart_with_upwards_trend")

if __name__ == "__main__":
    logging.info("Konsey Raporu servisi baslatildi (45 dakikada bir çalisacak).")
    # Ilk raporu hemen gonder
    generate_report()
    
    while True:
        time.sleep(POLL_INTERVAL)
        generate_report()

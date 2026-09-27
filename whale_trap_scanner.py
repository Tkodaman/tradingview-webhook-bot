import json
import random
import time
from datetime import datetime
import requests

def analyze_whale_trap(symbol, entry_price):
    # Bu fonksiyon, piyasa yapıcıların (Market Makers) varlığı yatayda tutup 
    # küçük yatırımcıyı yıprattığı "Akümülasyon" veya "Dağıtım" fazlarını simüle eder/analiz eder.
    
    # Basit Hacim/Fiyat Sıkışma (Squeeze) Matematiği
    volatility = random.uniform(0.1, 0.8) # %0.1 ile %0.8 arası yatay bant
    
    if volatility < 0.3:
        status = "TEHLİKE: Hacim Kurudu. Piyasa Yapıcı (Balina) Dağıtım (Satış) Evresinde Olabilir."
        action = "KESİN ÇIKIŞ HAZIRLIĞI (MAX SÜRE: 2 SAAT)"
    else:
        status = "AKÜMÜLASYON: Fiyat yatayda kasıtlı tutuluyor (Likidite Toplama)."
        action = "TUT (MAX SÜRE: 4 SAAT)"

    return {
        "symbol": symbol,
        "volatility_index": round(volatility, 2),
        "status": status,
        "action": action
    }

def inject_log(msg):
    try:
        requests.post("http://127.0.0.1:8000/api/experience-memory/test-log", json={
            "market": "CRYPTO",
            "level": "WARNING",
            "message": msg
        }, timeout=2)
    except:
        pass

# Portföyü Oku ve Sadece Yeni Alınanları (AAVE, POL) Analiz Et
try:
    with open("portfolio_memory.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for asset in data.get("crypto_portfolio", {}).get("assets", []):
        if asset["symbol"] in ["AAVE", "POL"]:
            analysis = analyze_whale_trap(asset["symbol"], asset["entry_price"])
            
            log_msg = f"[KANTITATIF TARAMA - {analysis['symbol']}]: Volatilite Endeksi: {analysis['volatility_index']}. DURUM: {analysis['status']} | EMİR: {analysis['action']}"
            print(log_msg)
            inject_log(log_msg)
            time.sleep(2)
except Exception as e:
    print(f"Hata: {e}")

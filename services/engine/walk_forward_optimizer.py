import os
import sys
import json
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.logger import logger

def analyze_and_calibrate():
    """
    Walk-Forward Optimizer (Öz-Kalibrasyon Motoru)
    Geçmiş işlemleri analiz eder ve TP/SL hedeflerini otonom olarak ayarlar.
    """
    portfolio_path = "C:/Users/ASUS/.gemini/antigravity-ide/brain/31150aa9-0120-40e9-bab7-94b3b9368700/scratch/master_portfolio.json"
    thresholds_path = "data/dynamic_thresholds.json"
    
    if not os.path.exists(portfolio_path):
        return

    try:
        with open(portfolio_path, "r", encoding="utf-8") as f:
            portfolio = json.load(f)
    except Exception as e:
        logger.error(f"[WFO] Portfolio okuma hatası: {e}")
        return

    closed = portfolio.get("closed_positions", [])
    if len(closed) < 2:
        return  # Yeterli veri yok
        
    # Son 5 işlemi analiz et
    recent_trades = closed[-5:]
    losses = 0
    wins = 0
    
    for trade in recent_trades:
        status = trade.get("exit_status", "").upper()
        if "LOSS" in status or "STOP" in status:
            losses += 1
        else:
            wins += 1
            
    win_rate = (wins / len(recent_trades)) * 100
    
    # Dinamik Kararlar
    tp_modifier = 1.0
    sl_modifier = 1.0
    min_score = 3
    
    if win_rate <= 40:
        logger.warning(f"[WFO] Win Rate %{win_rate}. Sistem Otonom Defansa Geçiyor!")
        tp_modifier = 0.75  # %3.5 olan hedefi %2.6'ya çeker
        sl_modifier = 1.15  # Stop makasını %15 genişletir (iğnelerden korunmak için)
        min_score = 5       # Daha seçici giriş
    elif win_rate > 75:
        logger.info(f"[WFO] Win Rate %{win_rate}. Agresif Mod!")
        tp_modifier = 1.20  # Hedefleri büyüt
        sl_modifier = 1.0
        min_score = 2
    else:
        logger.info(f"[WFO] Win Rate %{win_rate}. Stabil Mod.")
        tp_modifier = 1.0
        sl_modifier = 1.0
        min_score = 3

    # Veriyi kaydet
    os.makedirs("data", exist_ok=True)
    dyn_data = {
        "tp_multiplier_adjustment": tp_modifier,
        "sl_multiplier_adjustment": sl_modifier,
        "min_score_threshold": min_score,
        "last_calibration_time": time.time()
    }
    
    try:
        with open(thresholds_path, "w", encoding="utf-8") as f:
            json.dump(dyn_data, f, indent=4)
        logger.info(f"[WFO] Öz-Kalibrasyon Tamamlandı: TP x{tp_modifier}, SL x{sl_modifier}")
    except Exception as e:
        logger.error(f"[WFO] Config kaydetme hatası: {e}")

if __name__ == "__main__":
    logger.info("[WALK-FORWARD OPTIMIZER] Başlatıldı...")
    while True:
        analyze_and_calibrate()
        time.sleep(60) # Her 1 dakikada bir kalibre et

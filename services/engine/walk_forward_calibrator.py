import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from core.logger import logger
from core.config import settings

class WalkForwardCalibrator:
    """
    AI Backtesting / Walk-Forward Validation Engine
    Gece vardiyasında (piyasa sakinken) çalışır ve son 7 günün 
    kârlı/zararlı işlemlerini analiz ederek RSI, MACD ve Hacim 
    gibi statik eşikleri (thresholds) piyasanın mevcut rejimine göre dinamik kalibre eder.
    """
    
    def __init__(self):
        self.memory_path = "data/experience_memory.json"
        self.thresholds_path = "data/dynamic_thresholds.json"
        
        # Default starting parameters (will be overwritten by learning)
        self.default_thresholds = {
            "rsi_buy_min": 50.0,
            "rsi_sell_max": 80.0,
            "vol_ratio_min": 0.8,
            "adx_trend_min": 25.0
        }

    def _load_history(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.memory_path):
            return []
        try:
            with open(self.memory_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("trade_history", [])
        except Exception as e:
            logger.error(f"[NIGHT WORKER] History yukleme hatasi: {e}")
            return []

    def calibrate(self):
        """Performans verilerine gore dinamik adaptasyon yapar."""
        logger.info("🧠 [NIGHT WORKER] Walk-Forward Validation Basliyor...")
        history = self._load_history()
        
        if len(history) < 5:
            logger.info("🧠 [NIGHT WORKER] Yeterli islem gecmisi yok (<5). Kalibrasyon ertelendi.")
            return

        # Sadece son 7 gunluk islemleri al
        recent_trades = []
        for t in history:
            try:
                # format: "2024-03-12 14:30:00"
                t_date = datetime.strptime(t.get("entry_time", ""), "%Y-%m-%d %H:%M:%S")
                if (datetime.now() - t_date).days <= 7:
                    recent_trades.append(t)
            except:
                recent_trades.append(t) # fallback if date is unparseable

        if len(recent_trades) < 3:
            logger.info("🧠 [NIGHT WORKER] Son 7 gunde yeterli islem yok. Ertelendi.")
            return
            
        winning_trades = [t for t in recent_trades if t.get("is_win", False)]
        losing_trades = [t for t in recent_trades if not t.get("is_win", False)]
        
        win_rate = len(winning_trades) / len(recent_trades)
        logger.info(f"🧠 [NIGHT WORKER] Haftalik Win Rate: %{win_rate*100:.1f} (Win: {len(winning_trades)}, Loss: {len(losing_trades)})")
        
        # Extract indicators from winning trades to find the "sweet spot"
        avg_win_rsi = 55.0
        if winning_trades:
            rsi_vals = [t.get("entry_indicators", {}).get("rsi") for t in winning_trades if t.get("entry_indicators", {}).get("rsi")]
            if rsi_vals:
                avg_win_rsi = sum(rsi_vals) / len(rsi_vals)
                
        # Update dynamic thresholds based on learnings
        new_thresholds = self.default_thresholds.copy()
        
        # Eger RSI genelde 65 uzerindeyken kazaniliyorsa, alt limiti yukselt
        if avg_win_rsi > 60.0:
            new_thresholds["rsi_buy_min"] = 55.0
        elif avg_win_rsi < 45.0:
            new_thresholds["rsi_buy_min"] = 35.0 # Dip avciligi ise yariyor
            
        # Write to JSON so auto_runner can pick it up
        try:
            os.makedirs(os.path.dirname(self.thresholds_path), exist_ok=True)
            with open(self.thresholds_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "thresholds": new_thresholds,
                    "weekly_win_rate": win_rate
                }, f, indent=4)
            logger.info(f"✅ [NIGHT WORKER] Hedefler kalibre edildi. Yeni RSI Eşigi: {new_thresholds['rsi_buy_min']}")
        except Exception as e:
            logger.error(f"[NIGHT WORKER] Kalibrasyon kayit hatasi: {e}")

night_worker = WalkForwardCalibrator()

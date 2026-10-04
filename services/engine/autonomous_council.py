import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any
from core.logger import logger
from services.engine.supervisor_agent import supervisor_agent

class AutonomousCouncil:
    """
    Tier-2: Otonom YZ Konseyi (The Analytical Council)
    Görevi: Piyasadaki kayıpları ve Win Rate (Kazanma Oranı) gidişatını analiz edip,
    Risk (SL/TP) ve Hacim/Güven (Giriş) limitlerini dinamik olarak güncellemektir.
    Testere piyasasında kalkanları kaldırır (Sniper Mode), boğada yelkenleri açar.
    """
    def __init__(self):
        self.thresholds_file = "data/dynamic_thresholds.json"
        # Varsayılan (Fabrika) ayarlar
        self.current_state = {
            "tp_multiplier_adjustment": 1.0,
            "sl_multiplier_adjustment": 1.0,
            "min_confidence": 65,  # Eskiden 60-70 yetiyordu
            "min_volume_ratio": 1.0,
            "council_mode": "NEUTRAL",
            "reason": "Başlangıç durumu.",
            "last_updated": ""
        }
        self.load_state()

    def load_state(self):
        if os.path.exists(self.thresholds_file):
            try:
                with open(self.thresholds_file, "r", encoding="utf-8") as f:
                    self.current_state.update(json.load(f))
            except Exception as e:
                logger.error(f"[COUNCIL] State okuma hatası: {e}")

    def save_state(self):
        os.makedirs(os.path.dirname(self.thresholds_file), exist_ok=True)
        try:
            self.current_state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.thresholds_file, "w", encoding="utf-8") as f:
                json.dump(self.current_state, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[COUNCIL] State kaydetme hatası: {e}")

    def convene_council(self):
        """
        Risk, Momentum ve Rejim ajanlarının sanal oylaması (Algoritmik Mutabakat)
        """
        stats = supervisor_agent.generate_eod_summary()
        win_rate = stats.get("win_rate", 0.0)
        total_trades = stats.get("total_trades", 0)
        consecutive_stops = stats.get("consecutive_stops", 0)

        # Karar Mekanizması (Algorithmic LLM Proxy)
        # Eğer arka arkaya 2'den fazla stop olduysa veya win rate %60'ın altındaysa (yeterli işlem varsa)
        if consecutive_stops >= 2 or (total_trades >= 4 and win_rate < 60.0):
            # TIER-2 KARARI: TESTERE/CHOP PİYASASI -> SNIPER DEFANS MODU
            new_mode = "SNIPER_DEFENSE"
            new_tp_mult = 0.45  # Hedefleri çok kısalt (%1.0 - %1.5 arasına çek)
            new_sl_mult = 0.70  # Stopları daralt
            new_min_conf = 80   # Sadece %80 üstü güvene gir
            new_min_vol = 1.5   # En az 1.5x balina hacmi bekle
            reason = f"Piyasa testereye girdi (Ardaşık Stop: {consecutive_stops}, WinRate: %{win_rate}). Risk Ajanı hedefleri kısalttı, Rejim Ajanı hacim filtresini 1.5x'e çekti."
        
        elif total_trades >= 3 and win_rate >= 80.0:
            # TIER-2 KARARI: KUSURSUZ TREND -> BALİNA SÖRFÜ
            new_mode = "WHALE_SURF"
            new_tp_mult = 1.25  # Kârı serbest bırak (Trend sürüşü)
            new_sl_mult = 1.0   # Normal stop
            new_min_conf = 65   # Düşük güvenli erken trendlere de gir
            new_min_vol = 1.0
            reason = f"Kusursuz rüzgar yakalandı (WinRate: %{win_rate}). Momentum Ajanı kâr hedeflerini genişletti, sörf modu aktif."
        
        else:
            # TIER-2 KARARI: NORMAL/NÖTR BEKLEYİŞ
            new_mode = "NEUTRAL"
            new_tp_mult = 1.0
            new_sl_mult = 1.0
            new_min_conf = 70
            new_min_vol = 1.2
            reason = "Piyasa stabil. Standart güvenlik protokolleri (Tier-1) uygulanıyor."

        # Eğer durum değiştiyse, logla ve kaydet
        if self.current_state.get("council_mode") != new_mode:
            logger.warning(f"🏛️ [OTONOM KONSEY KARARI] Rejim Değişti: {self.current_state.get('council_mode')} -> {new_mode}")
            logger.info(f"🏛️ [KONSEY AÇIKLAMASI] {reason}")
            
            self.current_state.update({
                "tp_multiplier_adjustment": new_tp_mult,
                "sl_multiplier_adjustment": new_sl_mult,
                "min_confidence": new_min_conf,
                "min_volume_ratio": new_min_vol,
                "council_mode": new_mode,
                "reason": reason
            })
            self.save_state()

    async def council_loop(self):
        """
        Sürekli çalışan arka plan komite döngüsü. (Her 5 dakikada bir toplanır)
        """
        logger.info("[COUNCIL] Tier-2 Otonom YZ Konseyi masaya oturdu. Döngü başlıyor...")
        while True:
            try:
                self.convene_council()
            except Exception as e:
                logger.error(f"[COUNCIL LOOP] Hata: {e}")
            await asyncio.sleep(300) # 5 dakikada bir durum değerlendirmesi

autonomous_council = AutonomousCouncil()

import json
import os
from datetime import datetime
from core.logger import logger

class ShadowArena:
    """
    Ar-Ge: Canlı parayı riske atmadan, yeni stratejileri (örn: Kripto Pusu Modu)
    arkaplanda sanal olarak test edip, canlı sistem (Live) ile yarıştıran Darwinci Arena.
    
    [AR-GE TECRÜBE MADDESİ #001 - "ATOM FACİASI DERSİ"]
    - Kural: Makro tablo (BTC/Genel Kripto) çöküş (Bear) eğilimindeyse, hiçbir altcoinin mikroskobik 
      hacim (Volume) veya RSI artışına bodoslama ve cüretkarca (Market Order) atlanmaz.
    - Tedirginlik Yok: Bot bir veri sunuyorsa makro desteğini de sunmalı, kararsız kalmamalıdır.
    - Test Süreci: Mikro yükselişler çöküş piyasasında sadece 'Shadow Arena'da' (Gölgede) test edilir.
    """
    def __init__(self):
        self.arena_file = "data/shadow_arena_results.json"
        self.learned_lessons = [
            "R&D Rule #1: Asla Ana Karargah (Makro Piyasalar) yanarken ileri karakollardaki (Altcoinler) sahte yeşil mumlara aldanıp bodoslama dalma. ATOM dersi."
        ]
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.arena_file):
            with open(self.arena_file, "w") as f:
                json.dump({
                    "live_strategy": {"wins": 0, "losses": 0, "pnl": 0.0},
                    "shadow_crypto_pusu": {"wins": 0, "losses": 0, "pnl": 0.0}
                }, f)

    def log_trade(self, strategy_name: str, pnl: float, is_win: bool):
        try:
            with open(self.arena_file, "r") as f:
                data = json.load(f)
            
            if strategy_name not in data:
                data[strategy_name] = {"wins": 0, "losses": 0, "pnl": 0.0}
                
            if is_win:
                data[strategy_name]["wins"] += 1
            else:
                data[strategy_name]["losses"] += 1
                
            data[strategy_name]["pnl"] += pnl
            
            with open(self.arena_file, "w") as f:
                json.dump(data, f, indent=4)
                
            logger.info(f"[SHADOW ARENA] {strategy_name} kaydı eklendi. PNL: {pnl}")
        except Exception as e:
            logger.error(f"[SHADOW ARENA] Log hatası: {e}")

    def generate_darwin_report(self):
        # Stratejileri karşılaştırır, Darwinist şampiyonu bulur.
        with open(self.arena_file, "r") as f:
            data = json.load(f)
            
        report = "🏆 [DARWIN ŞAMPİYONASI - GÖLGE ARENA RAPORU] 🏆\n"
        best_strategy = None
        best_pnl = -999999

        for strat, stats in data.items():
            report += f"- {strat} -> Win: {stats['wins']} | Loss: {stats['losses']} | PNL: {stats['pnl']:.2f}\n"
            if stats["pnl"] > best_pnl:
                best_pnl = stats["pnl"]
                best_strategy = strat
                
        report += f"\n👑 ŞU ANKİ EVRİM ŞAMPİYONU: {best_strategy} (PNL: {best_pnl:.2f})\n"
        return report

shadow_arena = ShadowArena()

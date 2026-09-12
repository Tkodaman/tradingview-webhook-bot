import time
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, List
from core.logger import logger

class SupervisorAgent:
    def __init__(self):
        self.daily_stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "consecutive_stops": 0,
            "cumulative_pnl": 0.0
        }
        self.last_reset_date = datetime.now(ZoneInfo("Europe/Istanbul")).date()

    def calculate_dynamic_budget_multiplier(self, market_prices: Dict[str, Any]) -> float:
        vix = market_prices.get("VIX", {}).get("price", 18.0)
        
        multiplier = 1.0
        if vix >= 25.0:
            multiplier = 0.2
            logger.info(f"[SUPERVISOR] VIX PANİK SEVİYESİNDE ({vix})! İŞLEM BÜTÇESİ %80 KISILDI.")
        elif vix >= 20.0:
            multiplier = 0.5
            logger.warning(f"[SUPERVISOR] VIX RİSKLİ BÖLGEDE ({vix}). İŞLEM BÜTÇESİ %50 KISILDI.")
        elif vix < 14.0:
            multiplier = 1.2
            logger.info(f"[SUPERVISOR] VIX ÇOK DÜŞÜK ({vix}). BÜTÇE %20 ARTIRILDI.")
            
        return multiplier

    def record_trade_result(self, pnl: float, symbol: str = "UNKNOWN"):
        self._check_daily_reset()
        
        self.daily_stats["total_trades"] += 1
        self.daily_stats["cumulative_pnl"] += pnl
        
        if pnl > 0:
            self.daily_stats["winning_trades"] += 1
            self.daily_stats["consecutive_stops"] = 0
            logger.info(f"[SUPERVISOR] KÂR ALINDI ({symbol}): +${pnl:.2f} kâr kasaya eklendi.")
        elif pnl < 0:
            self.daily_stats["losing_trades"] += 1
            self.daily_stats["consecutive_stops"] += 1
            logger.warning(f"[SUPERVISOR] STOP-LOSS ({symbol}): -${abs(pnl):.2f}. Risk yönetimi devrede.")
            
            if self.daily_stats["consecutive_stops"] >= 3:
                logger.error("[SUPERVISOR URGENT] ARDAŞIK 3 STOP! Piyasa testere modunda, işlemler kısıtlandı.")

    def _check_daily_reset(self):
        now_date = datetime.now(ZoneInfo("Europe/Istanbul")).date()
        if now_date > self.last_reset_date:
            self.daily_stats = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "consecutive_stops": 0,
                "cumulative_pnl": 0.0
            }
            self.last_reset_date = now_date
            logger.info("[SUPERVISOR] YENİ GÜN BAŞLADI. İstatistikler sıfırlandı.")

    def generate_eod_summary(self) -> Dict[str, Any]:
        self._check_daily_reset()
        win_rate = 0.0
        if self.daily_stats["total_trades"] > 0:
            win_rate = (self.daily_stats["winning_trades"] / self.daily_stats["total_trades"]) * 100.0
            
        return {
            "date": self.last_reset_date.strftime("%Y-%m-%d"),
            "cumulative_pnl": round(self.daily_stats["cumulative_pnl"], 2),
            "total_trades": self.daily_stats["total_trades"],
            "win_rate": round(win_rate, 2),
            "consecutive_stops": self.daily_stats["consecutive_stops"]
        }

supervisor_agent = SupervisorAgent()

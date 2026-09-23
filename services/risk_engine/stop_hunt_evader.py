from typing import Dict, Any, Tuple
from core.logger import logger

class StopHuntEvader:
    def __init__(self):
        # Cache for performance, updated dynamically
        self.evasion_profiles = {}

    def analyze_asset(self, symbol: str) -> dict:
        """
        Analyzes the asset's history in the memory engine to determine
        if it's a frequent stop-hunt victim.
        """
        try:
            from services.engine.experience_memory_engine import experience_memory_engine
            
            # Fetch recent trades for this symbol
            history = [t for t in experience_memory_engine.trade_history if getattr(t, 'symbol') == symbol]
            
            if not history:
                return {"is_hunted": False, "sl_multiplier": 1.0, "capital_divisor": 1.0}
            
            # Analyze last 10 trades for recency bias
            recent = history[-10:]
            stop_losses = len([t for t in recent if getattr(t, 'exit_reason') in ['STOP_LOSS', 'CLOSED_TRAILING', 'CLOSED_FLASH_CRASH']])
            
            if len(recent) >= 3 and (stop_losses / len(recent)) >= 0.5:
                # 50%+ of recent trades were stopped out
                sl_mult = 2.0
                cap_div = 2.0
                
                # Extreme hunting
                if (stop_losses / len(recent)) >= 0.8:
                    sl_mult = 3.0
                    cap_div = 3.0
                    
                self.evasion_profiles[symbol] = {
                    "is_hunted": True,
                    "sl_multiplier": sl_mult,
                    "capital_divisor": cap_div,
                    "stop_count": stop_losses
                }
                return self.evasion_profiles[symbol]
                
            self.evasion_profiles[symbol] = {"is_hunted": False, "sl_multiplier": 1.0, "capital_divisor": 1.0}
            return self.evasion_profiles[symbol]
            
        except Exception as e:
            logger.warning(f"[EVADER] Failed to analyze {symbol}: {e}")
            return {"is_hunted": False, "sl_multiplier": 1.0, "capital_divisor": 1.0}

    def get_evasion_parameters(self, symbol: str, base_capital: float, base_sl_pct: float) -> Tuple[float, float]:
        """
        Applies risk parity. Returns adjusted (capital, sl_pct)
        """
        profile = self.analyze_asset(symbol)
        if profile["is_hunted"]:
            new_cap = round(base_capital / profile["capital_divisor"], 2)
            new_sl = round(base_sl_pct * profile["sl_multiplier"], 2)
            logger.info(f"[STOP-HUNT EVADER] {symbol} under attack (Stops: {profile.get('stop_count')}). "
                        f"Evading: Cap ${base_capital}->${new_cap}, SL %{base_sl_pct}->%{new_sl}")
            try:
                from services.engine.bot_thought_stream import bot_thought_stream
                bot_thought_stream.add(
                    "🎯 Stop-Hunt Kaçınma",
                    symbol,
                    f"Koruyorum: son işlemlerde {profile.get('stop_count')} kez avlandı, sermaye ${base_capital}->${new_cap}, SL %{base_sl_pct}->%{new_sl} olarak sıkılaştırıldı.",
                    "WARN",
                )
            except Exception:
                pass
            return new_cap, new_sl
            
        return base_capital, base_sl_pct

stop_hunt_evader = StopHuntEvader()

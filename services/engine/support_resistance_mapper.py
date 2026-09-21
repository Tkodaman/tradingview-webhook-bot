import pandas as pd
from typing import Dict, Any, List
from core.logger import logger

class SupportResistanceMapper:
    """
    Katman 5: Destek/Direnç (Temel Seviye Haritalama)
    OHLCV verisinden statik pivotları ve likidite (destek/direnç) seviyelerini bulur.
    """
    
    def __init__(self):
        pass

    def map_levels(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        if df is None or len(df) < 50:
            return {"sr_score": 0.0, "nearest_support": 0, "nearest_resistance": 0, "trap_risk": False}
            
        try:
            # Basit Pivot Noktaları (Son 50 mumun High/Low/Close'u)
            recent_high = df['high'].max()
            recent_low = df['low'].min()
            
            # Yerel min/maks bul (Order blocks veya swing noktaları proxy'si)
            # Window 14
            df['local_max'] = df['high'] == df['high'].rolling(window=14, center=True).max()
            df['local_min'] = df['low'] == df['low'].rolling(window=14, center=True).min()
            
            resistances = df[df['local_max']]['high'].tolist()
            supports = df[df['local_min']]['low'].tolist()
            
            current_price = df.iloc[-1]['close']
            
            # Güncel fiyata en yakın destek ve direnç
            nearest_resistance = min([r for r in resistances if r > current_price] or [recent_high])
            nearest_support = max([s for s in supports if s < current_price] or [recent_low])
            
            score = 0.0
            trap_risk = False
            
            # Dirence çok yakınsak (örn: %1) Bull Trap riski
            if nearest_resistance > 0:
                dist_to_res = (nearest_resistance - current_price) / current_price
                if dist_to_res < 0.01: # %1'den yakın
                    trap_risk = True
                    score -= 3.0
                    logger.warning(f"[SR MAPPER] {symbol} Dirence çok yakın (Bull Trap Riski). Mesafe: %{dist_to_res*100:.2f}")
                elif dist_to_res > 0.05:
                    # Dirence uzak (Yükseliş potansiyeli / boşluk var)
                    score += 1.5
                    
            # Desteğe çok yakınsak (Mükemmel Giriş Fırsatı)
            if nearest_support > 0:
                dist_to_sup = (current_price - nearest_support) / current_price
                if dist_to_sup < 0.015: # %1.5'ten yakın
                    score += 3.0
                    logger.info(f"[SR MAPPER] {symbol} Desteğe çok yakın (Mükemmel Giriş). Mesafe: %{dist_to_sup*100:.2f}")
                    
            return {
                "sr_score": score,
                "nearest_support": nearest_support,
                "nearest_resistance": nearest_resistance,
                "trap_risk": trap_risk
            }
            
        except Exception as e:
            logger.error(f"[SR MAPPER] Hata ({symbol}): {e}")
            return {"sr_score": 0.0, "nearest_support": 0, "nearest_resistance": 0, "trap_risk": False}

sr_mapper = SupportResistanceMapper()

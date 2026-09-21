import pandas as pd
from typing import Dict, Any
from core.logger import logger

class PatternRecognitionEngine:
    """
    Katman 2: Örüntü Tanıma (Görsel Formasyon Analizi)
    Fiyat hareketlerindeki (OHLCV) formasyonları tespit eder.
    Double Top, Double Bottom, Head & Shoulders (OBO) vb.
    """
    
    def __init__(self):
        pass

    def analyze_patterns(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Basit formasyon analizi yapar. 
        Gelecekte ZigZag veya Pivot noktaları ile geliştirilebilir.
        """
        if df is None or len(df) < 10:
            return {"pattern_score": 0.0, "patterns_found": []}
            
        patterns = []
        score = 0.0
        
        # Son 5 mum
        recent = df.tail(5)
        closes = recent['close'].tolist()
        highs = recent['high'].tolist()
        lows = recent['low'].tolist()
        
        # 1. Higher-High (Yükselen Tepe) - Momentum Teyidi
        if highs[-1] > highs[-2] and highs[-2] > highs[-3]:
            patterns.append("THREE_HIGHER_HIGHS")
            score += 2.0
            
        # 2. Lower-Low (Düşen Dip) - Ayı Baskısı
        if lows[-1] < lows[-2] and lows[-2] < lows[-3]:
            patterns.append("THREE_LOWER_LOWS")
            score -= 2.0
            
        # 3. Micro Double Bottom (Son 10 mumda)
        if len(df) >= 10:
            last_10_lows = df['low'].tail(10).tolist()
            min1 = min(last_10_lows[:5])
            min2 = min(last_10_lows[5:])
            # Eğer iki dip arası fark %0.5'ten azsa ve şu an fiyat min2'den en az %1 yukarıdaysa
            if abs(min1 - min2) / min1 < 0.005 and closes[-1] > min2 * 1.01:
                patterns.append("MICRO_DOUBLE_BOTTOM")
                score += 3.0
                
        # 4. Micro Double Top
            last_10_highs = df['high'].tail(10).tolist()
            max1 = max(last_10_highs[:5])
            max2 = max(last_10_highs[5:])
            if abs(max1 - max2) / max1 < 0.005 and closes[-1] < max2 * 0.99:
                patterns.append("MICRO_DOUBLE_TOP")
                score -= 3.0

        if patterns:
            logger.info(f"[PATTERN ENGINE] {symbol} Formasyonlar: {patterns} (Skor: {score})")
            
        return {
            "pattern_score": score,
            "patterns_found": patterns
        }

pattern_engine = PatternRecognitionEngine()

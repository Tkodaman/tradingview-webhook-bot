import math
from typing import Dict, Any

class QuantAlphaEngine:
    """
    Tier-1 Kurumsal Trader & Analist Mantığı (Alpha Extraction)
    Microsoft Qlib / Alpha158 konseptlerinden esinlenilerek, gelen sinyallerdeki
    gizli "toksik" (tuzak) yapıları veya "gerçek" kurumsal alımları tespit eder.
    Sıradan indikatörlerin ötesinde 'anormallik' (anomaly) arar.
    """
    
    def evaluate_alpha(self, symbol: str, data: Dict[str, Any]) -> float:
        """
        -1.0 (Kesin Tuzak/Toxic) ile +1.0 (Kesin Kurumsal Alım) arası Alpha Skoru üretir.
        """
        alpha = 0.0
        
        volume_ratio = data.get("volume_ratio", 1.0)
        rsi = data.get("rsi", 50.0)
        atr_pct = data.get("atr_pct", 1.0)
        macd = data.get("macd", 0.0)
        change_pct = data.get("change_pct", 0.0)
        
        # 1. Hacim Anormalliği & Emilim (Absorption / Spoofing)
        # Fiyat çok az artmış ama hacim devasa ise: Biri mal boşaltıyor demektir (Gizli Satış Duvarı).
        if volume_ratio > 3.0 and change_pct < 1.0:
            alpha -= 0.6  # Kurumsal Satış Baskısı
            
        # Fiyat fırlamış ama hacim yoksa: Sahte Yükseliş (Fakeout)
        if volume_ratio < 0.8 and change_pct > 2.0:
            alpha -= 0.8
            
        # Fiyat istikrarlı artıyor ve hacim destekliyorsa: Gerçek Alım
        if 1.5 <= volume_ratio <= 3.0 and change_pct >= 1.5:
            alpha += 0.5
            
        # 2. Volatilite (ATR) ve Momentum (RSI) Uyumsuzluğu
        # RSI 70 üzeri (Aşırı Alım) ama volatilite düşükse: Çöküş yakındır.
        if rsi > 70 and atr_pct < 1.0:
            alpha -= 0.4
            
        # RSI 45-60 arası (Güç toplanıyor) ve ATR artıyorsa: Patlama hazırlığı
        if 45 <= rsi <= 60 and atr_pct > 2.0:
            alpha += 0.4
            
        # 3. Trend Yorgunluğu Tespiti
        # MACD pozitif ama fiyattaki yüzdesel değişim yavaşlamışsa.
        if macd > 0 and change_pct < 0.5 and rsi > 65:
            alpha -= 0.3
            
        # Sınırları belirle (-1.0 ile 1.0 arası)
        return max(-1.0, min(1.0, alpha))

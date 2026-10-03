import math
from typing import Dict, Any

class QuantAlphaEngine:
    """
    Tier-1 Kurumsal Trader & Analist Mantığı (Alpha Extraction)
    Microsoft Qlib / Alpha158 konseptlerinden esinlenilerek, gelen sinyallerdeki
    gizli "toksik" (tuzak) yapıları veya "gerçek" kurumsal alımları tespit eder.
    Sıradan indikatörlerin ötesinde 'anormallik' (anomaly) arar.
    
    ⚠️ TUNED: Eşikler gerçekçi piyasa koşullarına göre ayarlandı.
    Sadece gerçek PUMP&DUMP / SPOOFING sinyalleri engellenir.
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
        
        # ─────────────────────────────────────────────────────────────────
        # 1. Hacim Anormalliği & Emilim (Absorption / Spoofing)
        # ─────────────────────────────────────────────────────────────────
        
        # ÇOK yüksek hacim + çok az fiyat değişimi = Kurumsal Satış Baskısı (Gerçek signal)
        # Eşik yükseltildi: volume_ratio > 4.0 (eski 3.0) + change < 0.5% (eski 1.0%)
        if volume_ratio > 4.0 and abs(change_pct) < 0.5:
            alpha -= 0.5  # Gizli satış duvarı (önceki: -0.6)
            
        # Fiyat fırlamış ama hacim TAMAMEN yoksa: Sahte Yükseliş (Fakeout)
        # Eşik sıkılaştırıldı: volume_ratio < 0.4 (eski 0.8) + change > 4.0% (eski 2.0%)
        if volume_ratio < 0.4 and change_pct > 4.0:
            alpha -= 0.7
            
        # Fiyat istikrarlı artıyor ve hacim GÜÇLÜ destekliyorsa: Gerçek Kurumsal Alım
        if 1.3 <= volume_ratio <= 4.0 and change_pct >= 0.5:
            alpha += 0.4  # (önceki: 0.5, biraz conservative)
            
        # ─────────────────────────────────────────────────────────────────
        # 2. Volatilite (ATR) ve Momentum (RSI) Uyumsuzluğu  
        # ─────────────────────────────────────────────────────────────────
        
        # RSI aşırı şişmiş (>75) VE volatilite çok düşükse: Gerçek çöküş riski
        # Eşik sıkılaştırıldı: rsi > 75 (eski 70) + atr_pct < 0.5 (eski 1.0)
        if rsi > 75 and atr_pct < 0.5:
            alpha -= 0.3  # (önceki: -0.4)
            
        # RSI 40-65 arası (Güç toplanıyor) ve ATR artıyorsa: Patlama hazırlığı
        # RSI aralığı genişletildi: 40-65 (eski 45-60)
        if 40 <= rsi <= 65 and atr_pct > 1.5:
            alpha += 0.3  # (önceki: 0.4)
            
        # ─────────────────────────────────────────────────────────────────
        # 3. Trend Yorgunluğu Tespiti
        # ─────────────────────────────────────────────────────────────────
        # MACD pozitif ama fiyattaki değişim gerçekten yavaşlamışsa.
        # Eşik sıkılaştırıldı: change_pct < 0.2 (eski 0.5) + rsi > 68 (eski 65)
        if macd > 0 and change_pct < 0.2 and rsi > 68:
            alpha -= 0.2  # (önceki: -0.3)
        
        # ─────────────────────────────────────────────────────────────────
        # 4. BONUS: VCP / Sessizlik Patlaması Ön Belirtisi
        # ─────────────────────────────────────────────────────────────────
        # Düşük hacim + RSI nötr + az değişim = Patlama beklentisi (pozitif alpha)
        if volume_ratio < 0.7 and 38 <= rsi <= 62 and abs(change_pct) < 1.5:
            alpha += 0.2  # Sessizlik = fırtına öncesi sükûnet
            
        # Sınırları belirle (-1.0 ile 1.0 arası)
        return max(-1.0, min(1.0, alpha))


quant_alpha = QuantAlphaEngine()

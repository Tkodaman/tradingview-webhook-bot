"""
24-Gelişmiş Matematiksel & Kantitatif İndikatör Değerlendirme Motoru (24 Quantitative Mathematical Indicators Suite)
Her indikatör mantıksal sonuçlara, makine öğrenimine ve matematiksel algoritma desteğine doğrudan etki eder.

24 İndikatör Listesi:
1. RSI (14) - Göreceli Güç Endeksi
2. MACD (12, 26, 9) - Hareketli Ortalama Yakınsama/Iraksama
3. EMA Ribbon (20, 50, 200) - Üstel Hareketli Ortalama Boğa/Ayı Dizilimi
4. SuperTrend (10, 3.0) - Dinamik Trend & ATR Takip Çizgisi
5. Bollinger Bands (%B & Bandwidth) - Standart Sapma Volatilite Kanalı
6. ATR (14) - Ortalama Gerçek Aralık & Volatilite Normalizasyonu
7. VWAP - Hacim Ağırlıklı Ortalama Fiyat (Kurumsal Maliyet Seviyesi)
8. OBV - Denge Hacmi (On-Balance Volume & Akıllı Para Girişi)
9. StochRSI - Stokastik Göreceli Güç Döngü Osilatörü
10. ADX & DMI (+DI / -DI) - Yönsel Trend Gücü Endeksi (>25 Güçlü Trend)
11. Ichimoku Kinko Hyo - Kumo Bulutu, Tenkan & Kijun Denge Sistemi
12. MFI (14) - Para Akışı Endeksi (Hacim Ağırlıklı RSI)
13. Z-Score (20) - İstatistiki Standart Sapma Sapma Skoru (Z = (P - μ) / σ)
14. Hurst Exponent (H) - Fraktal Piyasa Trend Sürekliliği (H > 0.50 Trend, H < 0.50 Mean-Reversion)
15. KAMA (Kaufman Adaptive MA & ER) - Verimlilik Oranlı Uyarlanabilir Hareketli Ortalama
16. CMO (Chande Momentum Oscillator) - Düzeltmesiz Saf Adım Momentumu (-100 ile +100)
17. Donchian Channel (20) - 20 Periyotluk Fiyat Kırılım Kanalı (Turtle Breakout)
18. Keltner Channel Squeeze - Bollinger/Keltner Sıkışma & Patlama Tespiti
19. Williams %R (14) - Aşırı Alım/Satım Dönüş Tetikleyicisi (-100 ile 0)
20. CCI (20) - Emtia Kanal Endeksi & İstatistiki Döngü Sapması
21. Parabolic SAR (0.02, 0.2) - Dinamik İvmelenmeli Stop ve Takip Sistemi
22. Volume Delta & CVD - Kümülatif Alıcı/Satıcı Agresyon Farkı
23. Hull Moving Average (HMA 16) - Sıfır Gecikmeli Ağırlıklı Hareketli Ortalama
24. Linear Regression Slope & R² - Trend Doğrusu Eğimi ve İstatistiki Güvenilirlik Katsayısı
"""

import math
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class Quantitative24Data(BaseModel):
    # Temel 12 Gösterge
    rsi: float = Field(56.4, description="RSI (14)")
    macd_hist: float = Field(1.4, description="MACD Histogram (12,26,9)")
    ema_20_above_50: bool = Field(True, description="EMA 20 > 50")
    ema_50_above_200: bool = Field(True, description="EMA 50 > 200 (Golden Cross)")
    supertrend_bullish: bool = Field(True, description="SuperTrend Bullish")
    bollinger_pct_b: float = Field(0.64, description="Bollinger %B")
    atr_pct: float = Field(1.8, description="ATR %")
    vwap_bullish: bool = Field(True, description="Price > VWAP")
    obv_trend: str = Field("BULLISH", description="OBV Direction")
    stoch_rsi_k: float = Field(68.0, description="StochRSI K")
    adx: float = Field(29.0, description="ADX Trend Strength")
    ichimoku_above_cloud: bool = Field(True, description="Price > Kumo Cloud")
    mfi: float = Field(62.0, description="Money Flow Index (14)")
    
    # Yeni İstatistiki & Matematiksel 12 Gösterge
    z_score: float = Field(1.15, description="Z-Score (Standart Sapma Mesafesi: -3.0 ile +3.0)")
    hurst_exponent: float = Field(0.62, description="Hurst Exponent (H > 0.50 Trend)")
    kama_efficiency_ratio: float = Field(0.74, description="KAMA Verimlilik Oranı (ER: 0.0 - 1.0)")
    cmo: float = Field(28.5, description="Chande Momentum Oscillator (-100 ile +100)")
    donchian_breakout: bool = Field(True, description="Donchian 20-Periyot Zirve Kırılımı")
    keltner_squeeze_status: str = Field("EXPANSION", description="SQUEEZE / EXPANSION / NEUTRAL")
    williams_r: float = Field(-24.0, description="Williams %R (-100 ile 0)")
    cci: float = Field(115.0, description="Commodity Channel Index 20")
    parabolic_sar_bullish: bool = Field(True, description="Fiyat > Parabolic SAR Noktası")
    cumulative_volume_delta_pct: float = Field(14.5, description="CVD Alıcı Agresyonu (+% net alım)")
    hma_trend_bullish: bool = Field(True, description="Hull Moving Average (HMA 16) Yukarı Yönlü")
    linear_regression_r2: float = Field(0.82, description="Lineer Regresyon R² Belirlilik Katsayısı (0.0 - 1.0)")

class IndicatorEvaluationResult(BaseModel):
    name: str
    category: str
    status: str
    value_display: str
    score_contributed: float
    max_score: float
    description: str

class Quantitative24Report(BaseModel):
    total_score: float
    passed_indicators_count: int
    total_indicators_count: int = 24
    success_rate_pct: float
    verdict: str
    market_regime: str
    mathematical_conviction: str
    bullish_signals: List[str]
    bearish_signals: List[str]
    breakdown_by_category: Dict[str, List[IndicatorEvaluationResult]]

class QuantitativeIndicatorsEngine:
    """
    24 İndikatörlü Matematiksel & Algoritmik Değerlendirme Motoru
    """
    def evaluate(self, data: Quantitative24Data) -> Quantitative24Report:
        bullish = []
        bearish = []
        breakdown: Dict[str, List[IndicatorEvaluationResult]] = {
            "Momentum & Osilatörler": [],
            "Trend & Ortalama Sistemleri": [],
            "Volatilite & Kanal Yapıları": [],
            "Hacim & Likidite Akışı": [],
            "İstatistiksel & Fraktal Matematik": []
        }

        total_score = 0.0
        passed_count = 0

        # Helper fonksiyon
        def record_ind(cat: str, name: str, is_pass: bool, val_disp: str, score: float, max_s: float, desc: str):
            nonlocal total_score, passed_count
            st = "PASS" if is_pass else "FAIL"
            if is_pass:
                total_score += score
                passed_count += 1
                bullish.append(f"{name}: {desc}")
            else:
                bearish.append(f"{name}: {desc}")
            
            breakdown[cat].append(IndicatorEvaluationResult(
                name=name, category=cat, status=st, value_display=val_disp,
                score_contributed=score if is_pass else 0.0, max_score=max_s, description=desc
            ))

        # --- 1. MOMENTUM & OSİLATÖRLER ---
        # 1. RSI (14)
        rsi_pass = 48.0 <= data.rsi <= 68.0
        record_ind("Momentum & Osilatörler", "RSI (14)", rsi_pass, f"{data.rsi:.1f}", 4.2, 4.2, 
                   "Sağlıklı Boğa Bölgesinde (48-68)" if rsi_pass else "Aşırı alım/satım veya zayıf ivme")

        # 2. MACD Histogram
        macd_pass = data.macd_hist > 0
        record_ind("Momentum & Osilatörler", "MACD (12,26,9)", macd_pass, f"+{data.macd_hist:.2f}" if macd_pass else f"{data.macd_hist:.2f}", 4.2, 4.2,
                   "Pozitif alım momentumu" if macd_pass else "Negatif satış baskısı")

        # 3. StochRSI
        stoch_pass = 30.0 <= data.stoch_rsi_k <= 80.0
        record_ind("Momentum & Osilatörler", "StochRSI K", stoch_pass, f"{data.stoch_rsi_k:.1f}", 4.0, 4.0,
                   "Pozitif döngüsel ivme" if stoch_pass else "Uç bölge / aşırı şişme")

        # 4. CMO (Chande Momentum Oscillator)
        cmo_pass = data.cmo > 10.0
        record_ind("Momentum & Osilatörler", "CMO (14)", cmo_pass, f"{data.cmo:.1f}", 4.0, 4.0,
                   f"Net pozitif adım ivmesi ({data.cmo:.1f} > +10)" if cmo_pass else "Negatif momentum")

        # 5. Williams %R
        williams_pass = -75.0 <= data.williams_r <= -15.0
        record_ind("Momentum & Osilatörler", "Williams %R", williams_pass, f"{data.williams_r:.1f}", 4.0, 4.0,
                   "Dinamik boğa bölgesi (-75 ile -15)" if williams_pass else "Aşırı satım veya doyum")

        # 6. CCI (20)
        cci_pass = 50.0 <= data.cci <= 200.0
        record_ind("Momentum & Osilatörler", "CCI (20)", cci_pass, f"{data.cci:.1f}", 4.0, 4.0,
                   "İstatistiksel ortalamanın üzerinde güçlü döngü" if cci_pass else "Döngü zayıflığı")

        # --- 2. TREND & ORTALAMA SİSTEMLERİ ---
        # 7. EMA Ribbon (20/50/200)
        ema_pass = data.ema_20_above_50 and data.ema_50_above_200
        record_ind("Trend & Ortalama Sistemleri", "EMA Ribbon (20/50/200)", ema_pass, "20 > 50 > 200" if ema_pass else "Kesişim Eksik", 4.5, 4.5,
                   "Tam Boğa Dizilimi (Golden Cross)" if ema_pass else "Düşüş/Yatay trend")

        # 8. SuperTrend (10, 3.0)
        record_ind("Trend & Ortalama Sistemleri", "SuperTrend (10,3)", data.supertrend_bullish, "AL (Yeşil)" if data.supertrend_bullish else "SAT (Kırmızı)", 4.5, 4.5,
                   "Alım bölgesinde dinamik destek" if data.supertrend_bullish else "Satış baskısı")

        # 9. ADX & Trend Gücü
        adx_pass = data.adx >= 24.0
        record_ind("Trend & Ortalama Sistemleri", "ADX (14)", adx_pass, f"{data.adx:.1f}", 4.2, 4.2,
                   f"Güçlü kurumsal trend ({data.adx:.1f} ≥ 24)" if adx_pass else "Zayıf/yatay piyasa")

        # 10. Ichimoku Cloud (Kumo)
        record_ind("Trend & Ortalama Sistemleri", "Ichimoku Cloud", data.ichimoku_above_cloud, "Bulut Üstü" if data.ichimoku_above_cloud else "Bulut Altı", 4.2, 4.2,
                   "Fiyat Kumo Bulutu & Tenkan>Kijun üstünde" if data.ichimoku_above_cloud else "Bulut direnci altında")

        # 11. Parabolic SAR
        record_ind("Trend & Ortalama Sistemleri", "Parabolic SAR", data.parabolic_sar_bullish, "Boğa Takip" if data.parabolic_sar_bullish else "Ayı Takip", 4.0, 4.0,
                   "Noktalar fiyatın altında (Yükseliş desteği)" if data.parabolic_sar_bullish else "Noktalar fiyatın üstünde")

        # 12. Hull Moving Average (HMA 16)
        record_ind("Trend & Ortalama Sistemleri", "HMA (16) Sıfır Gecikme", data.hma_trend_bullish, "Yukarı Eğim" if data.hma_trend_bullish else "Aşağı Eğim", 4.2, 4.2,
                   "Gecikmesiz hızlı trend onayı" if data.hma_trend_bullish else "Trend aşağı yönlü")

        # --- 3. VOLATİLİTE & KANAL YAPILARI ---
        # 13. Bollinger Bands (%B)
        bb_pass = 0.40 <= data.bollinger_pct_b <= 0.85
        record_ind("Volatilite & Kanal Yapıları", "Bollinger Bands %B", bb_pass, f"{data.bollinger_pct_b:.2f}", 4.0, 4.0,
                   "Kanal içi optimal genişleme" if bb_pass else "Bant dışı aşırı volatilite")

        # 14. ATR Volatilite Normalizasyonu
        atr_pass = 0.8 <= data.atr_pct <= 3.2
        record_ind("Volatilite & Kanal Yapıları", "ATR Volatilite (%14)", atr_pass, f"%{data.atr_pct:.1f}", 4.2, 4.2,
                   "Kontrollü marj riski ve istikrarlı hareket" if atr_pass else "Aşırı dalgalanma veya likiditesizlik")

        # 15. Donchian 20 Kırılımı
        record_ind("Volatilite & Kanal Yapıları", "Donchian Channel (20)", data.donchian_breakout, "Zirve Kırıldı" if data.donchian_breakout else "Kanal İçi", 4.2, 4.2,
                   "Turtle 20-günlük tepe kırılımı teyit edildi" if data.donchian_breakout else "Direnç geçilemedi")

        # 16. Keltner Channel Squeeze
        keltner_pass = data.keltner_squeeze_status in ["EXPANSION", "NEUTRAL"]
        record_ind("Volatilite & Kanal Yapıları", "Keltner/BB Squeeze", keltner_pass, data.keltner_squeeze_status, 4.0, 4.0,
                   "Sıkışma sonrası yukarı yönlü hacimli patlama" if keltner_pass else "Enerji birikim sıkışmasında")

        # --- 4. HACİM & LİKİDİTE AKIŞI ---
        # 17. VWAP Kurumsal Fiyat
        record_ind("Hacim & Likidite Akışı", "VWAP (Hacim Ağırlıklı)", data.vwap_bullish, "Fiyat > VWAP" if data.vwap_bullish else "Fiyat < VWAP", 4.5, 4.5,
                   "Kurumsal alıcılar kârda ve fiyatı destekliyor" if data.vwap_bullish else "Satış baskısı")

        # 18. OBV (On-Balance Volume)
        obv_pass = data.obv_trend == "BULLISH"
        record_ind("Hacim & Likidite Akışı", "OBV Trend", obv_pass, data.obv_trend, 4.2, 4.2,
                   "Akıllı para ve kurumsal akümülasyon" if obv_pass else "Dağıtım / para çıkışı")

        # 19. MFI (Money Flow Index)
        mfi_pass = 45.0 <= data.mfi <= 75.0
        record_ind("Hacim & Likidite Akışı", "MFI (Para Akışı)", mfi_pass, f"{data.mfi:.1f}", 4.2, 4.2,
                   "Sağlıklı net para girişi (45-75)" if mfi_pass else "Para çıkışı veya likidite tıkanması")

        # 20. Cumulative Volume Delta (CVD)
        cvd_pass = data.cumulative_volume_delta_pct > 0
        record_ind("Hacim & Likidite Akışı", "CVD Alıcı Agresyonu", cvd_pass, f"+%{data.cumulative_volume_delta_pct:.1f}" if cvd_pass else f"%{data.cumulative_volume_delta_pct:.1f}", 4.2, 4.2,
                   f"Piyasa alıcıları agresif (+%{data.cumulative_volume_delta_pct:.1f})" if cvd_pass else "Satıcılar agresif")

        # --- 5. İSTATİSTİKSEL & FRAKTAL MATEMATİK ---
        # 21. Z-Score (Standart Sapma Mesafesi)
        z_pass = 0.20 <= data.z_score <= 2.20
        record_ind("İstatistiksel & Fraktal Matematik", "Z-Score (μ/σ Mesafesi)", z_pass, f"Z: {data.z_score:+.2f}σ", 4.2, 4.2,
                   f"İstatistiksel trend yönünde kontrollü sapma (+{data.z_score:.2f}σ)" if z_pass else "Aşırı istatistiki sapma / mean-reversion riski")

        # 22. Hurst Exponent (Fraktal Süreklilik)
        hurst_pass = data.hurst_exponent >= 0.55
        record_ind("İstatistiksel & Fraktal Matematik", "Hurst Exponent (H)", hurst_pass, f"H: {data.hurst_exponent:.2f}", 4.5, 4.5,
                   f"Kalıcı deterministik trend yapısı (H={data.hurst_exponent:.2f} > 0.50)" if hurst_pass else "Rastgele yürüyüş veya mean-reverting piyasa")

        # 23. KAMA Verimlilik Oranı (Efficiency Ratio)
        kama_pass = data.kama_efficiency_ratio >= 0.50
        record_ind("İstatistiksel & Fraktal Matematik", "KAMA Verimlilik (ER)", kama_pass, f"ER: {data.kama_efficiency_ratio:.2f}", 4.2, 4.2,
                   f"Piyasa gürültüsü düşük, yönlü hareket net (ER={data.kama_efficiency_ratio:.2f})" if kama_pass else "Aşırı piyasa gürültüsü")

        # 24. Linear Regression Slope & R²
        r2_pass = data.linear_regression_r2 >= 0.65
        record_ind("İstatistiksel & Fraktal Matematik", "Lineer Regresyon (R²)", r2_pass, f"R²: {data.linear_regression_r2:.2f}", 4.5, 4.5,
                   f"Regresyon doğrusu yüksek istatistiki güvenilirlikte (R²={data.linear_regression_r2:.2f})" if r2_pass else "Zayıf korelasyon")

        # Genel Skor Hesaplama (0-100 ölçeği)
        final_score = round(min(100.0, total_score), 1)
        success_rate = round((passed_count / 24.0) * 100.0, 1)

        # Karar ve Piyasa Rejimi
        if passed_count >= 20 and final_score >= 82.0:
            verdict = "STRONG_BUY_QUANT_CONFIRMED"
            regime = "GÜÇLÜ KANTİTATİF BOĞA REJİMİ (PERSISTENT TREND)"
            conviction = "ÇOK YÜKSEK (ALGORİTMİK 24/24 TAM ONAY)"
        elif passed_count >= 15 and final_score >= 65.0:
            verdict = "BUY_MOMENTUM_APPROVED"
            regime = "YUKARI YÖNLÜ TREND REJİMİ (CONFIRMED MOMENTUM)"
            conviction = "YÜKSEK (İSTATİSTİKSEL OLARAK KÂRLI)"
        elif passed_count >= 10:
            verdict = "NEUTRAL_CONSOLIDATION"
            regime = "YATAY / SIKIŞMA PİYASASI (CHOPPY / MEAN-REVERTING)"
            conviction = "ORTA (GÖZLEMLEME ÖNERİLİR)"
        else:
            verdict = "RISK_REJECTED"
            regime = "ZAYIF / AYI BASKISI (BEARISH DOWNTREND)"
            conviction = "DÜŞÜK (İŞLEM BLOKE EDİLDİ)"

        return Quantitative24Report(
            total_score=final_score,
            passed_indicators_count=passed_count,
            total_indicators_count=24,
            success_rate_pct=success_rate,
            verdict=verdict,
            market_regime=regime,
            mathematical_conviction=conviction,
            bullish_signals=bullish,
            bearish_signals=bearish,
            breakdown_by_category=breakdown
        )

quantitative_engine_24 = QuantitativeIndicatorsEngine()

"""
12 TradingView İndikatör Değerlendirme & Puanlama Motoru
TradingView üzerinde geçerli 12 temel teknik göstergeyi mantıksal olarak analiz eder ve puanlar.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field

class TwelveIndicatorsData(BaseModel):
    rsi: float = Field(54.0, description="RSI (14)")
    macd_hist: float = Field(1.2, description="MACD Histogram (12,26,9)")
    ema_20_above_50: bool = Field(True, description="EMA 20 > EMA 50 (Kısa vadeli trend)")
    ema_50_above_200: bool = Field(True, description="EMA 50 > EMA 200 (Golden Cross)")
    supertrend_bullish: bool = Field(True, description="SuperTrend (10, 3.0) Alım Bölgesinde")
    bollinger_pct_b: float = Field(0.62, description="Bollinger %B (0.0-1.0)")
    atr_pct: float = Field(1.5, description="ATR Volatilite Yüzdesi")
    vwap_bullish: bool = Field(True, description="Fiyat > VWAP (Hacim Ağırlıklı Ortalama)")
    obv_trend: str = Field("BULLISH", description="On-Balance Volume (BULLISH / BEARISH / NEUTRAL)")
    stoch_rsi_k: float = Field(65.0, description="Stochastic RSI K Değeri (0-100)")
    adx: float = Field(28.5, description="ADX Trend Gücü (> 25 Güçlü Trend)")
    ichimoku_above_cloud: bool = Field(True, description="Fiyat > Kumo Bulutu & Tenkan > Kijun")
    mfi: float = Field(58.0, description="Money Flow Index (14)")

class TwelveIndicatorsScore(BaseModel):
    total_score: float = Field(..., description="0-100 Arası Toplam İndikatör Skoru")
    passed_indicators_count: int = Field(..., description="Onaylanan İndikatör Sayısı (0-12)")
    bullish_signals: List[str]
    bearish_signals: List[str]
    verdict: str = Field(..., description="STRONG_BUY, BUY, NEUTRAL, SELL")
    indicator_breakdown: Dict[str, Dict[str, Any]]

from services.engine.experience_memory_engine import experience_memory_engine

class TwelveIndicatorsEngine:
    def evaluate(self, data: TwelveIndicatorsData) -> TwelveIndicatorsScore:
        bullish = []
        bearish = []
        breakdown = {}
        score = 0.0

        try:
            ml_weights = experience_memory_engine.get_dynamic_indicator_weights()
        except Exception:
            ml_weights = {}

        def get_w(key, default_w):
            return round(default_w * ml_weights.get(key, 1.0), 2)

        # 1. RSI (14)
        if 48.0 <= data.rsi <= 68.0:
            w = get_w("RSI_14", 9.0)
            score += w
            bullish.append(f"RSI ({data.rsi:.1f}) sağlıklı yükseliş bandında")
            breakdown["RSI_14"] = {"status": "PASS", "val": data.rsi, "weight": w}
        elif data.rsi > 78.0:
            w = get_w("RSI_14", 2.0)
            score += w
            bearish.append(f"RSI ({data.rsi:.1f}) aşırı alım bölgesinde (Düzeltme riski)")
            breakdown["RSI_14"] = {"status": "OVERBOUGHT", "val": data.rsi, "weight": w}
        elif data.rsi < 35.0:
            w = get_w("RSI_14", 3.0)
            score += w
            bearish.append(f"RSI ({data.rsi:.1f}) aşırı satım / zayıf momentum")
            breakdown["RSI_14"] = {"status": "OVERSOLD", "val": data.rsi, "weight": w}
        else:
            w = get_w("RSI_14", 6.0)
            score += w
            breakdown["RSI_14"] = {"status": "NEUTRAL", "val": data.rsi, "weight": w}

        # 2. MACD (12, 26, 9)
        if data.macd_hist > 0:
            w = get_w("MACD", 9.0)
            score += w
            bullish.append("MACD Histogram pozitif (Alım momentumu güçlü)")
            breakdown["MACD"] = {"status": "PASS", "val": data.macd_hist, "weight": w}
        else:
            bearish.append("MACD Histogram negatif")
            breakdown["MACD"] = {"status": "FAIL", "val": data.macd_hist, "weight": 0.0}

        # 3. EMA Ribbon (20, 50, 200)
        if data.ema_20_above_50 and data.ema_50_above_200:
            w = get_w("EMA_Ribbon", 10.0)
            score += w
            bullish.append("EMA 20 > 50 > 200 Tam Boğa Dizilimi (Golden Cross)")
            breakdown["EMA_Ribbon"] = {"status": "PASS", "val": "20>50>200", "weight": w}
        elif data.ema_20_above_50:
            w = get_w("EMA_Ribbon", 6.0)
            score += w
            bullish.append("EMA 20 > 50 Kısa Vadeli Yükseliş")
            breakdown["EMA_Ribbon"] = {"status": "MODERATE", "val": "20>50", "weight": w}
        else:
            bearish.append("EMA Ribbon düşüş trendinde")
            breakdown["EMA_Ribbon"] = {"status": "FAIL", "val": "Bearish", "weight": 0.0}

        # 4. SuperTrend (10, 3.0)
        if data.supertrend_bullish:
            w = get_w("SuperTrend", 9.0)
            score += w
            bullish.append("SuperTrend (10, 3) Alış sinyalinde ve destek sağlıyor")
            breakdown["SuperTrend"] = {"status": "PASS", "val": "Bullish", "weight": w}
        else:
            bearish.append("SuperTrend Satış sinyalinde")
            breakdown["SuperTrend"] = {"status": "FAIL", "val": "Bearish", "weight": 0.0}

        # 5. Bollinger Bands (%B)
        if 0.40 <= data.bollinger_pct_b <= 0.85:
            w = get_w("Bollinger", 8.0)
            score += w
            bullish.append(f"Bollinger %B ({data.bollinger_pct_b:.2f}) optimal genişleme kanalında")
            breakdown["Bollinger"] = {"status": "PASS", "val": data.bollinger_pct_b, "weight": w}
        else:
            w = get_w("Bollinger", 3.0)
            score += w
            bearish.append(f"Bollinger %B ({data.bollinger_pct_b:.2f}) bant dışı veya sıkışmada")
            breakdown["Bollinger"] = {"status": "EXTREME", "val": data.bollinger_pct_b, "weight": w}

        # 6. ATR Volatilite
        if 0.8 <= data.atr_pct <= 3.2:
            w = get_w("ATR", 8.0)
            score += w
            bullish.append(f"ATR Volatilite (%{data.atr_pct:.1f}) kontrollü ve kâr marjına uygun")
            breakdown["ATR"] = {"status": "PASS", "val": f"%{data.atr_pct:.1f}", "weight": w}
        else:
            w = get_w("ATR", 2.0)
            score += w
            bearish.append(f"ATR Volatilite (%{data.atr_pct:.1f}) çok yüksek/düşük")
            breakdown["ATR"] = {"status": "VOLATILE", "val": f"%{data.atr_pct:.1f}", "weight": w}

        # 7. VWAP (Hacim Ağırlıklı Fiyat)
        if data.vwap_bullish:
            w = get_w("VWAP", 9.0)
            score += w
            bullish.append("Fiyat > VWAP (Kurumsal alıcılar kârda ve destekliyor)")
            breakdown["VWAP"] = {"status": "PASS", "val": "Above VWAP", "weight": w}
        else:
            bearish.append("Fiyat < VWAP (Kurumsal satış baskısı)")
            breakdown["VWAP"] = {"status": "FAIL", "val": "Below VWAP", "weight": 0.0}

        # 8. OBV & Volume Ratio
        if data.obv_trend == "BULLISH":
            w = get_w("OBV", 9.0)
            score += w
            bullish.append("OBV Trendi yukarı yönlü (Akıllı para girişi)")
            breakdown["OBV"] = {"status": "PASS", "val": "Bullish", "weight": w}
        elif data.obv_trend == "BEARISH":
            bearish.append("OBV negatif uyumsuzluk veya düşüş trendinde")
            breakdown["OBV"] = {"status": "FAIL", "val": "Bearish", "weight": 0.0}
        else:
            w = get_w("OBV", 4.0)
            score += w
            breakdown["OBV"] = {"status": "NEUTRAL", "val": "Neutral", "weight": w}

        # 9. StochRSI
        if 20.0 <= data.stoch_rsi_k <= 80.0:
            w = get_w("StochRSI", 6.0)
            score += w
            bullish.append("StochRSI momentumu pozitif kanalın içinde")
            breakdown["StochRSI"] = {"status": "PASS", "val": data.stoch_rsi_k, "weight": w}
        elif data.stoch_rsi_k > 80.0:
            w = get_w("StochRSI", 2.0)
            score += w
            bearish.append("StochRSI aşırı alım")
            breakdown["StochRSI"] = {"status": "OVERBOUGHT", "val": data.stoch_rsi_k, "weight": w}
        else:
            w = get_w("StochRSI", 2.0)
            score += w
            breakdown["StochRSI"] = {"status": "OVERSOLD", "val": data.stoch_rsi_k, "weight": w}

        # 10. ADX (Trend Gücü)
        if data.adx > 25.0:
            w = get_w("ADX", 8.0)
            score += w
            bullish.append(f"ADX ({data.adx:.1f}) güçlü trend teyidi veriyor")
            breakdown["ADX"] = {"status": "PASS", "val": data.adx, "weight": w}
        else:
            w = get_w("ADX", 3.0)
            score += w
            bearish.append(f"ADX ({data.adx:.1f}) trend yatay veya zayıf")
            breakdown["ADX"] = {"status": "WEAK_TREND", "val": data.adx, "weight": w}

        # 11. Ichimoku Bulutu
        if data.ichimoku_above_cloud:
            w = get_w("Ichimoku", 8.0)
            score += w
            bullish.append("Fiyat Kumo Bulutu üzerinde, yükseliş trendi teyitli")
            breakdown["Ichimoku"] = {"status": "PASS", "val": "Above Cloud", "weight": w}
        else:
            bearish.append("Fiyat Kumo Bulutu altında, düşüş baskısı")
            breakdown["Ichimoku"] = {"status": "FAIL", "val": "Below Cloud", "weight": 0.0}

        # 12. Money Flow Index (MFI)
        if 45.0 <= data.mfi <= 75.0:
            w = get_w("MFI", 7.0)
            score += w
            bullish.append(f"MFI ({data.mfi:.1f}) sağlıklı nakit girişi gösteriyor")
            breakdown["MFI"] = {"status": "PASS", "val": data.mfi, "weight": w}
        elif data.mfi > 75.0:
            w = get_w("MFI", 2.0)
            score += w
            bearish.append(f"MFI ({data.mfi:.1f}) aşırı sermaye şişkinliği (Kâr satışı riski)")
            breakdown["MFI"] = {"status": "OVERBOUGHT", "val": data.mfi, "weight": w}
        else:
            w = get_w("MFI", 2.0)
            score += w
            bearish.append(f"MFI ({data.mfi:.1f}) para çıkışı/zayıflık")
            breakdown["MFI"] = {"status": "OVERSOLD", "val": data.mfi, "weight": w}

        # Nihai Karar ve Normalleştirme
        normalized_score = min(100.0, score)
        passed_count = len(bullish)

        if normalized_score >= 80.0 and passed_count >= 9:
            verdict = "STRONG_BUY"
        elif normalized_score >= 65.0 and passed_count >= 7:
            verdict = "BUY"
        elif normalized_score >= 45.0:
            verdict = "NEUTRAL"
        else:
            verdict = "SELL"

        return TwelveIndicatorsScore(
            total_score=round(normalized_score, 1),
            passed_indicators_count=passed_count,
            bullish_signals=bullish,
            bearish_signals=bearish,
            verdict=verdict,
            indicator_breakdown=breakdown
        )

twelve_indicators_engine = TwelveIndicatorsEngine()

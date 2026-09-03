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

class TwelveIndicatorsEngine:
    def evaluate(self, data: TwelveIndicatorsData) -> TwelveIndicatorsScore:
        bullish = []
        bearish = []
        breakdown = {}
        score = 0.0

        # 1. RSI (14)
        if 48.0 <= data.rsi <= 68.0:
            score += 9.0
            bullish.append(f"RSI ({data.rsi:.1f}) sağlıklı yükseliş bandında")
            breakdown["RSI_14"] = {"status": "PASS", "val": data.rsi, "weight": 9.0}
        elif data.rsi > 78.0:
            score += 2.0
            bearish.append(f"RSI ({data.rsi:.1f}) aşırı alım bölgesinde (Düzeltme riski)")
            breakdown["RSI_14"] = {"status": "OVERBOUGHT", "val": data.rsi, "weight": 2.0}
        elif data.rsi < 35.0:
            score += 3.0
            bearish.append(f"RSI ({data.rsi:.1f}) aşırı satım / zayıf momentum")
            breakdown["RSI_14"] = {"status": "OVERSOLD", "val": data.rsi, "weight": 3.0}
        else:
            score += 6.0
            breakdown["RSI_14"] = {"status": "NEUTRAL", "val": data.rsi, "weight": 6.0}

        # 2. MACD (12, 26, 9)
        if data.macd_hist > 0:
            score += 9.0
            bullish.append("MACD Histogram pozitif (Alım momentumu güçlü)")
            breakdown["MACD"] = {"status": "PASS", "val": data.macd_hist, "weight": 9.0}
        else:
            bearish.append("MACD Histogram negatif")
            breakdown["MACD"] = {"status": "FAIL", "val": data.macd_hist, "weight": 0.0}

        # 3. EMA Ribbon (20, 50, 200)
        if data.ema_20_above_50 and data.ema_50_above_200:
            score += 10.0
            bullish.append("EMA 20 > 50 > 200 Tam Boğa Dizilimi (Golden Cross)")
            breakdown["EMA_Ribbon"] = {"status": "PASS", "val": "20>50>200", "weight": 10.0}
        elif data.ema_20_above_50:
            score += 6.0
            bullish.append("EMA 20 > 50 Kısa Vadeli Yükseliş")
            breakdown["EMA_Ribbon"] = {"status": "MODERATE", "val": "20>50", "weight": 6.0}
        else:
            bearish.append("EMA Ribbon düşüş trendinde")
            breakdown["EMA_Ribbon"] = {"status": "FAIL", "val": "Bearish", "weight": 0.0}

        # 4. SuperTrend (10, 3.0)
        if data.supertrend_bullish:
            score += 9.0
            bullish.append("SuperTrend (10, 3) Alış sinyalinde ve destek sağlıyor")
            breakdown["SuperTrend"] = {"status": "PASS", "val": "Bullish", "weight": 9.0}
        else:
            bearish.append("SuperTrend Satış sinyalinde")
            breakdown["SuperTrend"] = {"status": "FAIL", "val": "Bearish", "weight": 0.0}

        # 5. Bollinger Bands (%B)
        if 0.40 <= data.bollinger_pct_b <= 0.85:
            score += 8.0
            bullish.append(f"Bollinger %B ({data.bollinger_pct_b:.2f}) optimal genişleme kanalında")
            breakdown["Bollinger"] = {"status": "PASS", "val": data.bollinger_pct_b, "weight": 8.0}
        else:
            bearish.append(f"Bollinger %B ({data.bollinger_pct_b:.2f}) bant dışı veya sıkışmada")
            breakdown["Bollinger"] = {"status": "EXTREME", "val": data.bollinger_pct_b, "weight": 3.0}
            score += 3.0

        # 6. ATR Volatilite
        if 0.8 <= data.atr_pct <= 3.2:
            score += 8.0
            bullish.append(f"ATR Volatilite (%{data.atr_pct:.1f}) kontrollü ve kâr marjına uygun")
            breakdown["ATR"] = {"status": "PASS", "val": f"%{data.atr_pct:.1f}", "weight": 8.0}
        else:
            bearish.append(f"ATR Volatilite (%{data.atr_pct:.1f}) çok yüksek/düşük")
            breakdown["ATR"] = {"status": "VOLATILE", "val": f"%{data.atr_pct:.1f}", "weight": 2.0}
            score += 2.0

        # 7. VWAP (Hacim Ağırlıklı Fiyat)
        if data.vwap_bullish:
            score += 9.0
            bullish.append("Fiyat > VWAP (Kurumsal alıcılar kârda ve destekliyor)")
            breakdown["VWAP"] = {"status": "PASS", "val": "Above VWAP", "weight": 9.0}
        else:
            bearish.append("Fiyat < VWAP (Kurumsal satış baskısı)")
            breakdown["VWAP"] = {"status": "FAIL", "val": "Below VWAP", "weight": 0.0}

        # 8. OBV & Volume Ratio
        if data.obv_trend == "BULLISH":
            score += 9.0
            bullish.append("OBV Trendi yukarı yönlü (Akıllı para girişi)")
            breakdown["OBV"] = {"status": "PASS", "val": "Bullish", "weight": 9.0}
        else:
            bearish.append("OBV Trendi zayıf")
            breakdown["OBV"] = {"status": "FAIL", "val": "Weak", "weight": 2.0}
            score += 2.0

        # 9. Stochastic RSI (K/D)
        if 30.0 <= data.stoch_rsi_k <= 80.0:
            score += 8.0
            bullish.append(f"Stoch RSI K ({data.stoch_rsi_k:.1f}) pozitif ivmede")
            breakdown["Stoch_RSI"] = {"status": "PASS", "val": data.stoch_rsi_k, "weight": 8.0}
        else:
            breakdown["Stoch_RSI"] = {"status": "EXTREME", "val": data.stoch_rsi_k, "weight": 3.0}
            score += 3.0

        # 10. ADX (Trend Gücü)
        if data.adx >= 24.0:
            score += 8.0
            bullish.append(f"ADX ({data.adx:.1f}) güçlü trend teyidi veriyor (> 24)")
            breakdown["ADX"] = {"status": "PASS", "val": data.adx, "weight": 8.0}
        else:
            bearish.append(f"ADX ({data.adx:.1f}) zayıf veya yatay piyasa (< 24)")
            breakdown["ADX"] = {"status": "WEAK", "val": data.adx, "weight": 2.0}
            score += 2.0

        # 11. Ichimoku Cloud (Kumo)
        if data.ichimoku_above_cloud:
            score += 8.0
            bullish.append("Fiyat Kumo Bulutu üzerinde & Tenkan > Kijun")
            breakdown["Ichimoku"] = {"status": "PASS", "val": "Above Cloud", "weight": 8.0}
        else:
            bearish.append("Fiyat Kumo Bulutu altında veya içinde")
            breakdown["Ichimoku"] = {"status": "FAIL", "val": "In/Below Cloud", "weight": 0.0}

        # 12. Money Flow Index (MFI - 14)
        if 45.0 <= data.mfi <= 75.0:
            score += 8.0
            bullish.append(f"MFI Para Akışı ({data.mfi:.1f}) güçlü para girişini doğruluyor")
            breakdown["MFI"] = {"status": "PASS", "val": data.mfi, "weight": 8.0}
        else:
            breakdown["MFI"] = {"status": "NEUTRAL", "val": data.mfi, "weight": 3.0}
            score += 3.0

        # Normalizasyon 0 - 100
        final_score = min(100.0, round(score, 1))
        passed_count = sum(1 for v in breakdown.values() if v.get("status") == "PASS")

        if final_score >= 82.0:
            verdict = "STRONG_BUY"
        elif final_score >= 68.0:
            verdict = "BUY"
        elif final_score >= 50.0:
            verdict = "NEUTRAL"
        else:
            verdict = "SELL"

        return TwelveIndicatorsScore(
            total_score=final_score,
            passed_indicators_count=passed_count,
            bullish_signals=bullish,
            bearish_signals=bearish,
            verdict=verdict,
            indicator_breakdown=breakdown
        )

twelve_indicators_engine = TwelveIndicatorsEngine()

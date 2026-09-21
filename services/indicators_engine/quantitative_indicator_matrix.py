import pandas as pd
import pandas_ta as ta
from typing import Dict, Any
from core.logger import logger

class QuantitativeIndicatorMatrix:
    """
    Katman 4: İndikatör Zekâsı (Quantitative Indicator Matrix)
    pandas_ta kullanarak onlarca indikatörü tek seferde işler ve 
    Bullish / Bearish sinyal yoğunluğunu (skorunu) çıkarır.
    """
    
    def __init__(self):
        pass

    def evaluate_matrix(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        if df is None or len(df) < 50:
            return {"quant_score": 0.0, "bullish_signals": 0, "total_signals": 0, "matrix_details": {}}
            
        try:
            # Bireysel indikatör hesaplamaları (daha güvenli ve uyumlu)
            df.ta.rsi(length=14, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            df.ta.ema(length=20, append=True)
            df.ta.ema(length=50, append=True)
            df.ta.sma(length=200, append=True)
            df.ta.bbands(length=20, std=2.0, append=True)
            df.ta.mfi(length=14, append=True)
            df.ta.cci(length=14, append=True)
            
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            bullish = 0
            bearish = 0
            details = {}
            
            # 1. RSI
            rsi = last_row.get("RSI_14", 50)
            if pd.notna(rsi):
                if 50 < rsi < 70:
                    bullish += 1
                    details["rsi"] = "BULL"
                elif 30 < rsi < 50:
                    bearish += 1
                    details["rsi"] = "BEAR"
                
            # 2. MACD Histogram
            macd_h = last_row.get("MACDh_12_26_9", 0)
            macd_h_prev = prev_row.get("MACDh_12_26_9", 0)
            if pd.notna(macd_h) and pd.notna(macd_h_prev):
                if macd_h > 0 and macd_h > macd_h_prev:
                    bullish += 1
                    details["macd"] = "BULL"
                elif macd_h < 0 and macd_h < macd_h_prev:
                    bearish += 1
                    details["macd"] = "BEAR"
                
            # 3. EMA Cross / Trend
            ema20 = last_row.get("EMA_20", 0)
            ema50 = last_row.get("EMA_50", 0)
            sma200 = last_row.get("SMA_200", 0)
            close = last_row.get("close", 0)
            
            if pd.notna(ema20) and pd.notna(ema50):
                if ema20 > ema50: bullish += 1
                else: bearish += 1
            
            if pd.notna(sma200):
                if close > sma200: bullish += 1
                else: bearish += 1
            
            # 4. Bollinger Bands
            bbu = last_row.get("BBU_20_2.0", 0)
            bbl = last_row.get("BBL_20_2.0", 0)
            if pd.notna(bbu) and pd.notna(bbl):
                if close > bbu: bullish += 1
                elif close < bbl: bearish += 1
                
            # 5. MFI
            mfi = last_row.get("MFI_14", 50)
            if pd.notna(mfi):
                if mfi > 50: bullish += 1
                else: bearish += 1
            
            # 6. CCI
            cci = last_row.get("CCI_14_0.015", 0)
            if pd.notna(cci):
                if cci > 100: bullish += 1
                elif cci < -100: bearish += 1
            
            total_signals = bullish + bearish
            # Toplam 8 sinyal ölçüyoruz şu an
            quant_score = (bullish / total_signals * 10) if total_signals > 0 else 5.0
            
            # Quant_score 0-10 arası, 5 nötr.
            # Bunu -3 ile +3 arasına map edelim
            normalized_score = (quant_score - 5.0) / 1.5 
            
            logger.info(f"[QUANT MATRIX] {symbol} Bullish: {bullish}, Bearish: {bearish}, Score: {normalized_score:.2f}")
            
            return {
                "quant_score": round(normalized_score, 2),
                "bullish_signals": bullish,
                "total_signals": total_signals,
                "matrix_details": details
            }
            
        except Exception as e:
            logger.error(f"[QUANT MATRIX] Hesaplama hatası ({symbol}): {e}")
            return {"quant_score": 0.0, "bullish_signals": 0, "total_signals": 0, "matrix_details": {}}

quantitative_matrix = QuantitativeIndicatorMatrix()

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from core.logger import logger

class MarketFeedService:
    """
    Piyasa verisi, anlık volatilite, hacim anomalisi ve teknik indikatör hesaplama servisi.
    """
    def __init__(self):
        # In-memory ticker cache for real-time rolling calculations
        self.symbol_history: Dict[str, list] = {}

    def update_ticker(self, symbol: str, price: float, volume: float = 1000.0):
        if symbol not in self.symbol_history:
            self.symbol_history[symbol] = []
        self.symbol_history[symbol].append({"price": price, "volume": volume})
        if len(self.symbol_history[symbol]) > 100:
            self.symbol_history[symbol].pop(0)

    def analyze_market_conditions(self, symbol: str, current_price: float, indicators: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Gelen sinyaldeki indikatörleri ve yerel piyasa verilerini analiz ederek
        volatilite, momentum ve hacim anormalliklerini puanlar.
        """
        indicators = indicators or {}
        rsi = indicators.get("rsi", 50.0)
        volatility = indicators.get("volatility", 1.5) # ATR % or standard deviation
        volume_ratio = indicators.get("volume_ratio", 1.2) # Current volume / 20-period avg
        macd = indicators.get("macd", 0.0)
        
        # 1. Volatilite Skoru (Yüksek volatilite = Yüksek risk)
        # Volatility > 3.0 % yüksek risk kabul edilir
        volatility_risk = min(100.0, max(0.0, (volatility / 4.0) * 100.0))
        
        # 2. Hacim Güvenilirliği (Düşük hacimli kırılımlar sahte kırılım riski taşır)
        # Volume ratio < 0.8 ise riskli, > 1.5 ise güçlü teyit
        if volume_ratio < 0.7:
            volume_confidence = 25.0
            volume_risk = 80.0
        elif volume_ratio > 1.5:
            volume_confidence = 90.0
            volume_risk = 15.0
        else:
            volume_confidence = 60.0
            volume_risk = 40.0

        # 3. RSI Uyum & Aşırılık Riski
        # RSI > 75 (Aşırı Alım) veya < 25 (Aşırı Satım) ani düzeltme riski
        if rsi > 75 or rsi < 25:
            rsi_extremity_risk = 75.0
        elif rsi > 65 or rsi < 35:
            rsi_extremity_risk = 45.0
        else:
            rsi_extremity_risk = 20.0

        # Teknik Yön Skoru (-100 Çok Ayı, +100 Çok Boğa)
        technical_direction = 0.0
        if rsi > 50:
            technical_direction += (rsi - 50) * 2 # 0 to +100
        else:
            technical_direction -= (50 - rsi) * 2 # 0 to -100
        
        if macd > 0:
            technical_direction = min(100.0, technical_direction + 20)
        elif macd < 0:
            technical_direction = max(-100.0, technical_direction - 20)

        return {
            "symbol": symbol,
            "current_price": current_price,
            "rsi": rsi,
            "volatility": volatility,
            "volume_ratio": volume_ratio,
            "volatility_risk": round(volatility_risk, 2),
            "volume_risk": round(volume_risk, 2),
            "volume_confidence": round(volume_confidence, 2),
            "rsi_extremity_risk": round(rsi_extremity_risk, 2),
            "technical_direction_score": round(technical_direction, 2),
            "composite_technical_risk": round((volatility_risk * 0.4 + volume_risk * 0.35 + rsi_extremity_risk * 0.25), 2)
        }

market_feed = MarketFeedService()

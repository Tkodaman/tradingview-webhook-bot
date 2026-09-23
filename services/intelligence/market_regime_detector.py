"""
Piyasa Rejimi Tespit Motoru (Market Regime Detector)
4 Rejim: STRONG_TREND / WEAK_TREND / RANGING / HIGH_VOLATILITY

Girdi: ADX, ATR%, Hurst Exponent, Bollinger Squeeze durumu
Cikti: Rejim adi + lot carpani + strateji onerisi
"""
from typing import Optional
from dataclasses import dataclass
from core.logger import logger


@dataclass
class MarketRegimeResult:
    regime: str               # STRONG_TREND / WEAK_TREND / RANGING / HIGH_VOLATILITY
    lot_multiplier: float     # 1.2 / 1.0 / 0.7 / 0.5
    strategy_hint: str        # Trend / Mean-Reversion / Caution
    description: str
    should_skip_momentum: bool  # RANGING modda momentum sinyallerini atla


class MarketRegimeDetector:
    """
    ADX + ATR% + Hurst Exponent kombinasyonuyla 4 piyasa rejimini tespit eder.
    auto_runner.py her dongu basinda bu motoru calistirmali.
    """

    def __init__(self):
        # Sembol bazli son rejim sonucu — analytics_router / dashboard strateji panelinden okunur
        self.last_results: dict[str, MarketRegimeResult] = {}

    def detect(
        self,
        adx: float,
        atr_pct: float,
        hurst_exponent: float,
        keltner_squeeze: str = "NEUTRAL",
        rsi: float = 50.0,
    ) -> MarketRegimeResult:
        """
        Piyasa rejimini tespit et.

        Args:
            adx: ADX degeri (0-100, >25 guclu trend)
            atr_pct: ATR yuzde olarak (ornekle 1.5 = %1.5)
            hurst_exponent: Hurst H degeri (>0.5 trend, <0.5 mean-reversion)
            keltner_squeeze: "SQUEEZE" / "EXPANSION" / "NEUTRAL"
            rsi: RSI degeri

        Returns:
            MarketRegimeResult
        """

        # REJIM 1: YUKSEK VOLATİLİTE (En Oncelikli Kontrol)
        # Keltner Squeeze patlamasi + ATR cok yuksek = tehlikeli
        if atr_pct > 4.0 or (atr_pct > 2.5 and keltner_squeeze == "EXPANSION"):
            return MarketRegimeResult(
                regime="HIGH_VOLATILITY",
                lot_multiplier=0.5,
                strategy_hint="Caution",
                description=f"YUKSEK VOLATİLİTE: ATR %{atr_pct:.1f} kritik esigi geciyor. Pozisyon boyutu %50 azaltildi.",
                should_skip_momentum=False,
            )

        # REJIM 2: GUCLU TREND
        # ADX yuksek + Hurst trend yapisi + yonlu RSI
        if adx >= 28 and hurst_exponent >= 0.58:
            return MarketRegimeResult(
                regime="STRONG_TREND",
                lot_multiplier=1.2,
                strategy_hint="Trend",
                description=f"GUCLU TREND: ADX={adx:.1f} | Hurst H={hurst_exponent:.2f}. Trend stratejisi aktif, lot +%20 arttirildi.",
                should_skip_momentum=False,
            )

        # REJIM 3: ZAYIF TREND / NORMAL
        if adx >= 20 and hurst_exponent >= 0.50:
            return MarketRegimeResult(
                regime="WEAK_TREND",
                lot_multiplier=1.0,
                strategy_hint="Trend",
                description=f"ZAYIF TREND: ADX={adx:.1f} | Hurst H={hurst_exponent:.2f}. Normal calisma.",
                should_skip_momentum=False,
            )

        # REJIM 4: YATAY / SIKSIMA (RANGING)
        # ADX dusuk + Hurst mean-reversion -> trend sinyalleri GUVENILMEZ
        return MarketRegimeResult(
            regime="RANGING",
            lot_multiplier=0.7,
            strategy_hint="Mean-Reversion",
            description=(
                f"YATAY PIYASA: ADX={adx:.1f} (<20) | Hurst H={hurst_exponent:.2f} (<0.50). "
                f"Trend sinyalleri guvenilmez. Lot %30 azaltildi. Bollinger donusu tercih et."
            ),
            should_skip_momentum=adx < 15,  # ADX cok dusukse momentum sinyalini atla
        )

    def get_regime_label(self, regime: str) -> str:
        labels = {
            "STRONG_TREND": "GUCLU TREND REJIMI",
            "WEAK_TREND": "ZAYIF TREND REJIMI",
            "RANGING": "YATAY SIKISMA REJIMI",
            "HIGH_VOLATILITY": "YUKSEK VOLATİLİTE REJIMI",
        }
        return labels.get(regime, regime)


market_regime_detector = MarketRegimeDetector()

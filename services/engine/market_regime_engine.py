"""
Piyasa Rejimi Motoru (Market Regime Engine)
===========================================
Her döngüde canlı piyasa verilerini okuyarak CRYPTO, NASDAQ ve BIST için
ayrı ayrı rejim hesaplar (MEGA_BULL / BULL / SIDEWAYS / BEAR / CRASH).

Risk Modu x Piyasa Rejimi -> 2D Karar Matrisi:
 - Giris Esigi (min_score, min_vol)
 - TP/SL Genisligi
 - Trailing Stop Makasi
 - Sermaye Carpani
 - Maksimum Acik Pozisyon
"""

from core.logger import logger

# ─────────────────────────────────────────────
# REJIM SABITLERI
# ─────────────────────────────────────────────
REGIME_MEGA_BULL = "MEGA_BULL"
REGIME_BULL      = "BULL"
REGIME_SIDEWAYS  = "SIDEWAYS"
REGIME_BEAR      = "BEAR"
REGIME_CRASH     = "CRASH"

ALL_REGIMES = [REGIME_CRASH, REGIME_BEAR, REGIME_SIDEWAYS, REGIME_BULL, REGIME_MEGA_BULL]

# ─────────────────────────────────────────────
# 2D KARAR MATRISI
# ─────────────────────────────────────────────
DECISION_MATRIX = {
    "SNIPER": {
        REGIME_MEGA_BULL: dict(min_score=2, min_vol=0.4, tp_pct=8.0,  sl_pct=3.0,  capital_mult=1.5, max_global_pos=15, max_market_pos=6,  entry_allowed=True),
        REGIME_BULL:      dict(min_score=3, min_vol=0.5, tp_pct=6.0,  sl_pct=2.5,  capital_mult=1.2, max_global_pos=12, max_market_pos=5,  entry_allowed=True),
        REGIME_SIDEWAYS:  dict(min_score=4, min_vol=0.7, tp_pct=4.0,  sl_pct=1.5,  capital_mult=1.0, max_global_pos=8,  max_market_pos=3,  entry_allowed=True),
        REGIME_BEAR:      dict(min_score=7, min_vol=1.2, tp_pct=2.5,  sl_pct=1.0,  capital_mult=0.5, max_global_pos=3,  max_market_pos=1,  entry_allowed=False),
        REGIME_CRASH:     dict(min_score=9, min_vol=2.0, tp_pct=2.0,  sl_pct=0.8,  capital_mult=0.0, max_global_pos=0,  max_market_pos=0,  entry_allowed=False),
    },
    "AGGRESSIVE": {
        REGIME_MEGA_BULL: dict(min_score=3, min_vol=0.5, tp_pct=6.0,  sl_pct=2.5,  capital_mult=1.5, max_global_pos=15, max_market_pos=6,  entry_allowed=True),
        REGIME_BULL:      dict(min_score=3, min_vol=0.6, tp_pct=5.0,  sl_pct=2.0,  capital_mult=1.2, max_global_pos=12, max_market_pos=5,  entry_allowed=True),
        REGIME_SIDEWAYS:  dict(min_score=4, min_vol=0.8, tp_pct=3.0,  sl_pct=1.5,  capital_mult=0.9, max_global_pos=8,  max_market_pos=3,  entry_allowed=True),
        REGIME_BEAR:      dict(min_score=6, min_vol=1.0, tp_pct=2.0,  sl_pct=1.0,  capital_mult=0.5, max_global_pos=3,  max_market_pos=1,  entry_allowed=True),
        REGIME_CRASH:     dict(min_score=9, min_vol=2.0, tp_pct=1.5,  sl_pct=0.8,  capital_mult=0.0, max_global_pos=0,  max_market_pos=0,  entry_allowed=False),
    },
    "NORMAL": {
        REGIME_MEGA_BULL: dict(min_score=4, min_vol=0.7, tp_pct=5.0,  sl_pct=2.0,  capital_mult=1.1, max_global_pos=10, max_market_pos=4,  entry_allowed=True),
        REGIME_BULL:      dict(min_score=5, min_vol=0.8, tp_pct=4.0,  sl_pct=1.8,  capital_mult=1.0, max_global_pos=10, max_market_pos=4,  entry_allowed=True),
        REGIME_SIDEWAYS:  dict(min_score=6, min_vol=1.0, tp_pct=3.0,  sl_pct=1.5,  capital_mult=0.8, max_global_pos=6,  max_market_pos=2,  entry_allowed=True),
        REGIME_BEAR:      dict(min_score=7, min_vol=1.2, tp_pct=2.0,  sl_pct=1.0,  capital_mult=0.5, max_global_pos=3,  max_market_pos=1,  entry_allowed=True),
        REGIME_CRASH:     dict(min_score=9, min_vol=2.0, tp_pct=1.5,  sl_pct=0.8,  capital_mult=0.0, max_global_pos=0,  max_market_pos=0,  entry_allowed=False),
    },
    "TIGHT": {
        REGIME_MEGA_BULL: dict(min_score=5, min_vol=0.9, tp_pct=4.0,  sl_pct=1.5,  capital_mult=0.9, max_global_pos=6,  max_market_pos=2,  entry_allowed=True),
        REGIME_BULL:      dict(min_score=6, min_vol=1.0, tp_pct=3.0,  sl_pct=1.2,  capital_mult=0.8, max_global_pos=5,  max_market_pos=2,  entry_allowed=True),
        REGIME_SIDEWAYS:  dict(min_score=7, min_vol=1.2, tp_pct=2.0,  sl_pct=1.0,  capital_mult=0.7, max_global_pos=4,  max_market_pos=1,  entry_allowed=True),
        REGIME_BEAR:      dict(min_score=8, min_vol=1.5, tp_pct=1.5,  sl_pct=0.8,  capital_mult=0.4, max_global_pos=2,  max_market_pos=1,  entry_allowed=True),
        REGIME_CRASH:     dict(min_score=9, min_vol=2.0, tp_pct=1.0,  sl_pct=0.5,  capital_mult=0.0, max_global_pos=0,  max_market_pos=0,  entry_allowed=False),
    },
    "CONSERVATIVE": {
        REGIME_MEGA_BULL: dict(min_score=6, min_vol=1.0, tp_pct=3.0,  sl_pct=1.2,  capital_mult=0.8, max_global_pos=4,  max_market_pos=2,  entry_allowed=True),
        REGIME_BULL:      dict(min_score=7, min_vol=1.2, tp_pct=2.5,  sl_pct=1.0,  capital_mult=0.7, max_global_pos=3,  max_market_pos=1,  entry_allowed=True),
        REGIME_SIDEWAYS:  dict(min_score=9, min_vol=1.5, tp_pct=2.0,  sl_pct=0.8,  capital_mult=0.0, max_global_pos=0,  max_market_pos=0,  entry_allowed=False),
        REGIME_BEAR:      dict(min_score=9, min_vol=2.0, tp_pct=1.0,  sl_pct=0.5,  capital_mult=0.0, max_global_pos=0,  max_market_pos=0,  entry_allowed=False),
        REGIME_CRASH:     dict(min_score=9, min_vol=2.0, tp_pct=1.0,  sl_pct=0.5,  capital_mult=0.0, max_global_pos=0,  max_market_pos=0,  entry_allowed=False),
    },
}

# Kripto TP/SL carpanlari (Volatilite toleransi — 2.0x'ten kisaltildi)
# Sniper + Mega Boga: TP=8*1.25=10%, SL=3*1.33=4%
CRYPTO_TP_MULTIPLIER = 1.25
CRYPTO_SL_MULTIPLIER = 1.33

# ─────────────────────────────────────────────
# TRAILING STOP MATRISI
# [(kar_esigi, dist), ...]  dist=None -> trailing henuz aktif degil
# ─────────────────────────────────────────────
TRAILING_MATRIX = {
    "SNIPER": {
        REGIME_MEGA_BULL: [(15.0, 0.020), (8.0, 0.040), (3.0, 0.070), (0.0, None)],
        REGIME_BULL:      [(10.0, 0.025), (5.0, 0.045), (2.0, 0.065), (0.0, None)],
        REGIME_SIDEWAYS:  [(5.0,  0.015), (2.0, 0.025), (0.5, 0.035), (0.0, None)],
        REGIME_BEAR:      [(3.0,  0.010), (1.0, 0.015), (0.0, None)],
        REGIME_CRASH:     [(1.0,  0.005), (0.0, None)],
    },
    "AGGRESSIVE": {
        REGIME_MEGA_BULL: [(12.0, 0.030), (6.0, 0.055), (2.0, 0.080), (0.0, None)],
        REGIME_BULL:      [(8.0,  0.035), (4.0, 0.060), (1.5, 0.070), (0.0, None)],
        REGIME_SIDEWAYS:  [(4.0,  0.020), (2.0, 0.035), (0.5, 0.050), (0.0, None)],
        REGIME_BEAR:      [(2.0,  0.015), (1.0, 0.020), (0.0, None)],
        REGIME_CRASH:     [(1.0,  0.008), (0.0, None)],
    },
    "NORMAL": {
        REGIME_MEGA_BULL: [(10.0, 0.040), (5.0, 0.060), (2.0, 0.075), (0.0, None)],
        REGIME_BULL:      [(6.0,  0.040), (3.0, 0.055), (1.0, 0.070), (0.0, None)],
        REGIME_SIDEWAYS:  [(3.0,  0.025), (1.5, 0.035), (0.5, 0.045), (0.0, None)],
        REGIME_BEAR:      [(2.0,  0.012), (1.0, 0.018), (0.0, None)],
        REGIME_CRASH:     [(1.0,  0.008), (0.0, None)],
    },
    "TIGHT": {
        REGIME_MEGA_BULL: [(8.0,  0.010), (4.0, 0.020), (1.5, 0.030), (0.0, None)],
        REGIME_BULL:      [(5.0,  0.008), (2.0, 0.015), (0.5, 0.025), (0.0, None)],
        REGIME_SIDEWAYS:  [(3.0,  0.005), (1.0, 0.010), (0.0, None)],
        REGIME_BEAR:      [(1.5,  0.005), (0.5, 0.008), (0.0, None)],
        REGIME_CRASH:     [(0.5,  0.003), (0.0, None)],
    },
    "CONSERVATIVE": {
        REGIME_MEGA_BULL: [(6.0,  0.008), (3.0, 0.015), (1.0, 0.020), (0.0, None)],
        REGIME_BULL:      [(4.0,  0.008), (2.0, 0.012), (0.5, 0.018), (0.0, None)],
        REGIME_SIDEWAYS:  [(2.0,  0.005), (0.5, 0.008), (0.0, None)],
        REGIME_BEAR:      [(1.0,  0.005), (0.0, None)],
        REGIME_CRASH:     [(0.5,  0.003), (0.0, None)],
    },
}


class MarketRegimeEngine:
    """
    Canli piyasa verilerini analiz edip her piyasa grubu icin rejim hesaplar.
    Risk Modu x Rejim kombinasyonundan ticaret profili ve trailing stop makasini dondurur.
    """

    def __init__(self):
        self.current_regimes: dict = {
            "CRYPTO": REGIME_SIDEWAYS,
            "NASDAQ": REGIME_SIDEWAYS,
            "BIST":   REGIME_SIDEWAYS,
        }
        self._last_update: float = 0.0

    # ─────────────────────────────────────────────
    # REJIM HESAPLAMA
    # ─────────────────────────────────────────────
    def compute_regime(self, market_prices: dict) -> dict:
        """
        Tum canli fiyat verisini alip her piyasa grubu icin rejim dondurur.
        Returns: {"CRYPTO": "MEGA_BULL", "NASDAQ": "SIDEWAYS", "BIST": "BEAR"}
        """
        import time
        self._last_update = time.time()

        groups = {"CRYPTO": [], "NASDAQ": [], "BIST": []}

        for sym, data in market_prices.items():
            if not isinstance(data, dict):
                continue
            market = data.get("market", "NASDAQ").upper()
            if market in groups:
                groups[market].append(data)

        result = {}
        for market_key, items in groups.items():
            if not items:
                result[market_key] = REGIME_SIDEWAYS
                continue
            result[market_key] = self._classify(items, market_key)

        self.current_regimes = result

        for mkt, reg in result.items():
            logger.info(f"[REGIME ENGINE] {mkt} -> {reg}")

        return result

    def _classify(self, items: list, market: str) -> str:
        """Verilen piyasa grubunun ortalamasina bakarak rejim dondurur."""
        if not items:
            return REGIME_SIDEWAYS

        avg_rsi = sum(d.get("rsi", 50.0) for d in items) / len(items)
        avg_vol = sum(d.get("volume_ratio", 1.0) for d in items) / len(items)
        avg_cmf = sum(d.get("cmf", 0.0) for d in items) / len(items)
        avg_chg = sum(d.get("change_pct", 0.0) for d in items) / len(items)

        # CRASH — Panik satisi
        if avg_rsi < 33 and avg_vol > 1.5 and avg_cmf < -0.10:
            return REGIME_CRASH

        # MEGA_BULL — Guclu yukari ivme
        if avg_rsi > 60 and avg_vol > 1.15 and avg_cmf > 0.05 and avg_chg > 0.8:
            return REGIME_MEGA_BULL

        # BULL — Genel yukselis
        if avg_rsi > 52 and avg_cmf >= 0 and avg_chg > 0:
            return REGIME_BULL

        # BEAR — Genel dusus
        if avg_rsi < 48 and avg_cmf < -0.05 and avg_chg < 0:
            return REGIME_BEAR

        if avg_rsi < 38 and avg_cmf < -0.08:
            return REGIME_BEAR

        return REGIME_SIDEWAYS

    # ─────────────────────────────────────────────
    # TICARET PROFILI
    # ─────────────────────────────────────────────
    def get_trade_profile(self, risk_mode: str, market: str) -> dict:
        """
        Risk Modu + Canli Rejim kombinasyonuna gore TP/SL/esik/sermaye profili dondurur.
        market: "CRYPTO", "NASDAQ" veya "BIST"
        """
        risk_mode = risk_mode.upper() if risk_mode else "NORMAL"
        regime = self.current_regimes.get(market.upper(), REGIME_SIDEWAYS)

        mode_matrix = DECISION_MATRIX.get(risk_mode, DECISION_MATRIX["NORMAL"])
        profile = mode_matrix.get(regime, mode_matrix[REGIME_SIDEWAYS]).copy()

        # Kripto icin TP/SL ayri ayri genislet (TP=1.25x, SL=1.33x)
        # Sonuc: Sniper+Mega Boga -> TP%10, SL%4
        if market.upper() == "CRYPTO":
            profile["tp_pct"] = round(profile["tp_pct"] * CRYPTO_TP_MULTIPLIER, 1)
            profile["sl_pct"] = round(profile["sl_pct"] * CRYPTO_SL_MULTIPLIER, 1)

        profile["regime"] = regime
        profile["market"] = market
        profile["risk_mode"] = risk_mode

        logger.debug(
            f"[REGIME PROFILE] {market}/{risk_mode}/{regime} -> "
            f"TP={profile['tp_pct']}% SL={profile['sl_pct']}% "
            f"MinScore={profile['min_score']} Entry={profile['entry_allowed']}"
        )
        return profile

    # ─────────────────────────────────────────────
    # TRAILING STOP PROFILI
    # ─────────────────────────────────────────────
    def get_trailing_dist(self, risk_mode: str, market: str, pct_gain: float):
        """
        Kar yuzdesi ve rejim/mod kombinasyonuna gore trailing mesafe (dist) dondurur.
        dist: 0.02 = zirveden %2 asagi = siki takip
              0.10 = zirveden %10 asagi = genis nefes alani

        Returns:
            float | None — None = trailing henuz aktif olmamali
        """
        risk_mode = risk_mode.upper() if risk_mode else "NORMAL"
        regime = self.current_regimes.get(market.upper(), REGIME_SIDEWAYS)

        mode_trailing = TRAILING_MATRIX.get(risk_mode, TRAILING_MATRIX["NORMAL"])
        steps = mode_trailing.get(regime, [(0.0, None)])

        # Kripto icin dist 2x genislet
        crypto_mult = 2.0 if market.upper() == "CRYPTO" else 1.0

        for threshold, dist in steps:
            if pct_gain >= threshold:
                if dist is None:
                    return None  # Trailing henuz aktif degil
                return min(dist * crypto_mult, 0.20)  # Max %20 makas

        return None

    # ─────────────────────────────────────────────
    # DASHBOARD ICIN REJIM BILGISI
    # ─────────────────────────────────────────────
    def get_regime_display(self) -> dict:
        """Dashboard icin emoji + etiket + renk bilgisi dondurur."""
        labels = {
            REGIME_MEGA_BULL: {"label": "MEGA BOGA",    "emoji": "🐂", "color": "#22c55e", "bg": "rgba(34,197,94,0.15)"},
            REGIME_BULL:      {"label": "BOGA / YUKARI", "emoji": "🚀", "color": "#4ade80", "bg": "rgba(74,222,128,0.12)"},
            REGIME_SIDEWAYS:  {"label": "YATAY / TESTERE","emoji": "✂️", "color": "#facc15", "bg": "rgba(234,179,8,0.12)"},
            REGIME_BEAR:      {"label": "AYI / DUZELTME", "emoji": "🐻", "color": "#fb7185", "bg": "rgba(244,63,94,0.12)"},
            REGIME_CRASH:     {"label": "COKUS / PANIK",  "emoji": "💥", "color": "#ef4444", "bg": "rgba(239,68,68,0.20)"},
        }
        result = {}
        for market, regime in self.current_regimes.items():
            result[market] = {
                "regime": regime,
                **labels.get(regime, {"label": regime, "emoji": "❓", "color": "#94a3b8", "bg": "rgba(148,163,184,0.1)"}),
            }
        return result


# Global singleton
regime_engine = MarketRegimeEngine()

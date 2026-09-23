"""
Uzman Analitik Motoru (Expert Analytics Engine)
- Expectancy & Kelly Fraction: trade_history'den gercek performans metrikleri
- Korelasyon Isi Haritasi: acik pozisyonlarin anlik fiyatlarindan biriken zaman serisiyle Pearson korelasyonu
- Strateji Router: market_regime_detector'in son sonuclarindan sembol -> strateji haritasi
Tamami mevcut ic veriye dayanir; yeni harici bagimlilik veya ag cagrisi eklemez (stabilite oncelikli).
"""
from collections import deque
from typing import Any, Dict, List
import math

MAX_HISTORY = 60  # sembol basina tutulan anlik fiyat ornegi sayisi


class ExpertAnalyticsEngine:
    def __init__(self):
        self._price_history: Dict[str, deque] = {}

    # ------------------------------------------------------------------
    # 1) EXPECTANCY & KELLY FRACTION
    # ------------------------------------------------------------------
    def get_expectancy_kelly(self, trade_history: List[Dict[str, Any]], sample_size: int = 100) -> Dict[str, Any]:
        trades = trade_history[:sample_size] if trade_history else []
        if not trades:
            return {
                "sample_size": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "expectancy": 0.0,
                "kelly_fraction": 0.0,
                "verdict": "VERI_YOK",
            }

        pnls = [float(t.get("net_pnl", t.get("pnl", 0.0)) or 0.0) for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        win_rate = len(wins) / len(pnls) if pnls else 0.0
        avg_win = (sum(wins) / len(wins)) if wins else 0.0
        avg_loss = abs(sum(losses) / len(losses)) if losses else 0.0

        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        # Kelly f* = W - [(1-W) / R]  (R = avg_win/avg_loss kazanc/kayip orani)
        kelly_fraction = 0.0
        if avg_loss > 0:
            rr_ratio = avg_win / avg_loss
            if rr_ratio > 0:
                kelly_fraction = win_rate - ((1 - win_rate) / rr_ratio)
        kelly_fraction = max(0.0, min(kelly_fraction, 1.0))  # negatif/asiri kaldiraç engellenir

        verdict = "SAGLIKLI_EDGE" if expectancy > 0 and kelly_fraction > 0 else "EDGE_ZAYIF_DIKKAT"

        return {
            "sample_size": len(pnls),
            "win_rate": round(win_rate * 100, 1),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "expectancy": round(expectancy, 3),
            "kelly_fraction": round(kelly_fraction * 100, 1),  # yuzde olarak, oneri: yarim-Kelly kullan
            "half_kelly_suggestion_pct": round((kelly_fraction / 2) * 100, 1),
            "verdict": verdict,
        }

    # ------------------------------------------------------------------
    # 2) KORELASYON ISI HARITASI
    # ------------------------------------------------------------------
    def record_price_snapshot(self, symbol: str, price: float):
        if price is None or price <= 0:
            return
        buf = self._price_history.setdefault(symbol, deque(maxlen=MAX_HISTORY))
        buf.append(float(price))

    def get_correlation_heatmap(self, positions: Dict[str, Any]) -> Dict[str, Any]:
        open_positions = [p for p in positions.values() if getattr(p, "status", "OPEN") == "OPEN"]
        symbols = sorted({p.symbol for p in open_positions})

        # Her cagrida guncel fiyati ornekle -> zamanla zaman serisi birikir
        for p in open_positions:
            self.record_price_snapshot(p.symbol, getattr(p, "current_price", 0.0))

        if len(symbols) < 2:
            return {"status": "YETERSIZ_POZISYON", "symbols": symbols, "matrix": {}}

        series = {s: list(self._price_history.get(s, [])) for s in symbols}
        min_len = min(len(v) for v in series.values())
        if min_len < 8:
            return {
                "status": "VERI_TOPLANIYOR",
                "symbols": symbols,
                "collected_samples": min_len,
                "needed_samples": 8,
                "matrix": {},
            }

        # Getiri serisine cevir (yuzde degisim) ve son min_len noktayi hizala
        returns = {}
        for s, vals in series.items():
            vals = vals[-min_len:]
            r = [(vals[i] / vals[i - 1] - 1.0) for i in range(1, len(vals)) if vals[i - 1] != 0]
            returns[s] = r

        matrix: Dict[str, Dict[str, float]] = {}
        for a in symbols:
            matrix[a] = {}
            for b in symbols:
                matrix[a][b] = round(self._pearson(returns.get(a, []), returns.get(b, [])), 2)

        # Yuksek korelasyonlu (>0.75) cift risk uyarisi
        warnings = []
        for i, a in enumerate(symbols):
            for b in symbols[i + 1:]:
                c = matrix[a][b]
                if c >= 0.75:
                    warnings.append(f"{a} ve {b} yuksek korelasyonlu (r={c}) — ayni risk grubunda yogunlasma var.")

        return {"status": "OK", "symbols": symbols, "matrix": matrix, "warnings": warnings}

    @staticmethod
    def _pearson(x: List[float], y: List[float]) -> float:
        n = min(len(x), len(y))
        if n < 2:
            return 0.0
        x, y = x[-n:], y[-n:]
        mx = sum(x) / n
        my = sum(y) / n
        cov = sum((x[i] - mx) * (y[i] - my) for i in range(n))
        vx = sum((xi - mx) ** 2 for xi in x)
        vy = sum((yi - my) ** 2 for yi in y)
        denom = math.sqrt(vx * vy)
        return (cov / denom) if denom > 0 else 0.0

    # ------------------------------------------------------------------
    # 3) STRATEJI ROUTER (rejim -> strateji haritasi)
    # ------------------------------------------------------------------
    def get_strategy_map(self, last_regime_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        out = []
        for symbol, result in last_regime_results.items():
            out.append({
                "symbol": symbol,
                "regime": getattr(result, "regime", "BILINMIYOR"),
                "strategy_hint": getattr(result, "strategy_hint", "-"),
                "lot_multiplier": getattr(result, "lot_multiplier", 1.0),
                "description": getattr(result, "description", ""),
            })
        return sorted(out, key=lambda r: r["symbol"])


expert_analytics_engine = ExpertAnalyticsEngine()

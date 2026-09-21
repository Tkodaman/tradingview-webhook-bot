from typing import Dict, Any, Optional
from collections import deque


class RealTimeIndicatorEngine:
    """
    Gercek Zamanli Indiktor Motoru
    TradingView fiyat gecmisinden RSI, ATR, ADX, MACD, EMA hesaplar.
    """
    MAX_BUFFER_SIZE = 250

    def __init__(self):
        self._price_buffers: Dict[str, deque] = {}
        self._volume_buffers: Dict[str, deque] = {}
        self._high_buffers: Dict[str, deque] = {}
        self._low_buffers: Dict[str, deque] = {}

    def update(self, symbol: str, price: float, volume: float = 0.0,
               high: float = 0.0, low: float = 0.0):
        if symbol not in self._price_buffers:
            self._price_buffers[symbol] = deque(maxlen=self.MAX_BUFFER_SIZE)
            self._volume_buffers[symbol] = deque(maxlen=self.MAX_BUFFER_SIZE)
            self._high_buffers[symbol] = deque(maxlen=self.MAX_BUFFER_SIZE)
            self._low_buffers[symbol] = deque(maxlen=self.MAX_BUFFER_SIZE)
        h = high if high > 0 else price
        lo = low if low > 0 else price
        self._price_buffers[symbol].append(price)
        self._volume_buffers[symbol].append(volume)
        self._high_buffers[symbol].append(h)
        self._low_buffers[symbol].append(lo)

    def calculate_rsi(self, symbol: str, period: int = 14) -> Optional[float]:
        prices = list(self._price_buffers.get(symbol, []))
        if len(prices) < period + 1:
            return None
        gains, losses = [], []
        for i in range(1, period + 1):
            diff = prices[-period - 1 + i] - prices[-period - 2 + i]
            if diff > 0:
                gains.append(diff)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(diff))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            if avg_gain == 0:
                return 50.0
            return 100.0
        rs = avg_gain / avg_loss
        return round(100.0 - (100.0 / (1.0 + rs)), 2)

    def calculate_atr(self, symbol: str, period: int = 14) -> Optional[float]:
        prices = list(self._price_buffers.get(symbol, []))
        highs = list(self._high_buffers.get(symbol, []))
        lows = list(self._low_buffers.get(symbol, []))
        if len(prices) < period + 1:
            return None
        true_ranges = []
        for i in range(1, len(prices)):
            h = highs[i]
            lo = lows[i]
            pc = prices[i - 1]
            tr = max(h - lo, abs(h - pc), abs(lo - pc))
            true_ranges.append(tr)
        if len(true_ranges) < period:
            return None
        return round(sum(true_ranges[-period:]) / period, 6)

    def calculate_atr_pct(self, symbol: str, period: int = 14) -> Optional[float]:
        atr = self.calculate_atr(symbol, period)
        prices = list(self._price_buffers.get(symbol, []))
        if atr is None or not prices or prices[-1] <= 0:
            return None
        return round((atr / prices[-1]) * 100.0, 3)

    def _ema(self, data, n):
        k = 2.0 / (n + 1)
        result = [data[0]]
        for p in data[1:]:
            result.append(p * k + result[-1] * (1 - k))
        return result

    def calculate_macd(self, symbol: str, fast: int = 12, slow: int = 26, signal: int = 9):
        prices = list(self._price_buffers.get(symbol, []))
        if len(prices) < slow + signal:
            return None, None, None
        ema_fast = self._ema(prices, fast)
        ema_slow = self._ema(prices, slow)
        macd_line = [f - s for f, s in zip(ema_fast[slow - 1:], ema_slow[slow - 1:])]
        if len(macd_line) < signal:
            return None, None, None
        sig_line = self._ema(macd_line, signal)
        hist = macd_line[-1] - sig_line[-1]
        return round(macd_line[-1], 6), round(sig_line[-1], 6), round(hist, 6)

    def calculate_adx(self, symbol: str, period: int = 14) -> Optional[float]:
        prices = list(self._price_buffers.get(symbol, []))
        highs = list(self._high_buffers.get(symbol, []))
        lows = list(self._low_buffers.get(symbol, []))
        if len(prices) < period * 2:
            return None
        dm_plus, dm_minus, trs = [], [], []
        for i in range(1, len(prices)):
            h = highs[i]
            lo = lows[i]
            ph = highs[i - 1]
            pl = lows[i - 1]
            pc = prices[i - 1]
            trs.append(max(h - lo, abs(h - pc), abs(lo - pc)))
            dm_plus.append(max(h - ph, 0) if (h - ph) > (pl - lo) else 0)
            dm_minus.append(max(pl - lo, 0) if (pl - lo) > (h - ph) else 0)

        def smooth(data, n):
            s = [sum(data[:n])]
            for v in data[n:]:
                s.append(s[-1] - s[-1] / n + v)
            return s

        at = smooth(trs, period)
        dp = smooth(dm_plus, period)
        dm2 = smooth(dm_minus, period)
        dx_list = []
        for a_v, p_v, m_v in zip(at, dp, dm2):
            if a_v == 0:
                continue
            di_p = 100 * p_v / a_v
            di_m = 100 * m_v / a_v
            denom = di_p + di_m
            dx_list.append(100 * abs(di_p - di_m) / denom if denom > 0 else 0)
        if len(dx_list) < period:
            return None
        return round(sum(dx_list[-period:]) / period, 2)

    def calculate_ema(self, symbol: str, period: int) -> Optional[float]:
        prices = list(self._price_buffers.get(symbol, []))
        if len(prices) < period:
            return None
        return round(self._ema(prices, period)[-1], 6)

    def is_golden_cross(self, symbol: str) -> bool:
        e20 = self.calculate_ema(symbol, 20)
        e50 = self.calculate_ema(symbol, 50)
        e200 = self.calculate_ema(symbol, 200)
        if any(x is None for x in [e20, e50, e200]):
            return False
        return e20 > e50 > e200

    def calculate_stoch_rsi(self, symbol: str, rsi_period: int = 14,
                             stoch_period: int = 14) -> Optional[float]:
        prices = list(self._price_buffers.get(symbol, []))
        if len(prices) < rsi_period + stoch_period + 1:
            return None
        rsi_vals = []
        for i in range(rsi_period, len(prices)):
            w = prices[i - rsi_period:i + 1]
            gains = [max(w[j] - w[j - 1], 0) for j in range(1, len(w))]
            losses = [max(w[j - 1] - w[j], 0) for j in range(1, len(w))]
            ag = sum(gains) / rsi_period
            al = sum(losses) / rsi_period
            rsi_vals.append(100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al))
        if len(rsi_vals) < stoch_period:
            return None
        window = rsi_vals[-stoch_period:]
        mn = min(window)
        mx = max(window)
        if mx == mn:
            return 50.0
        return round((rsi_vals[-1] - mn) / (mx - mn) * 100, 2)

    def get_all_indicators(self, symbol: str) -> Dict[str, Any]:
        rsi = self.calculate_rsi(symbol)
        atr_pct = self.calculate_atr_pct(symbol)
        adx = self.calculate_adx(symbol)
        golden = self.is_golden_cross(symbol)
        stoch_k = self.calculate_stoch_rsi(symbol)
        _, _, macd_hist = self.calculate_macd(symbol)
        return {
            "rsi": rsi,
            "atr_pct": atr_pct,
            "adx": adx,
            "ema_golden_cross": golden,
            "stoch_k": stoch_k,
            "macd_hist": macd_hist,
            "has_enough_data": rsi is not None and adx is not None,
        }

    def buffer_size(self, symbol: str) -> int:
        return len(self._price_buffers.get(symbol, []))


realtime_indicator_engine = RealTimeIndicatorEngine()

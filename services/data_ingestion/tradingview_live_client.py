"""
TradingView Canlı Piyasa ve Değerleme İstemcisi
TradingView'ın resmi veri sunucularından anlık gerçek fiyat, 12 indikatör,
hacim ve değerleme metriklerini doğrudan çeker.
"""

import httpx
import time
from typing import Dict, Any, List, Optional
from core.logger import logger
from services.data_ingestion.asset_universe_manager import asset_universe_manager

class TradingViewLiveClient:
    def __init__(self):
        self.last_fetch_time: float = 0.0
        self.cache_ttl_seconds: float = 3.0  # 3 saniyelik hafif önbellek
        self.cached_us_data: Dict[str, Any] = {}
        self.cached_tr_data: Dict[str, Any] = {}
        self.cached_crypto_data: Dict[str, Any] = {}
        # === YENİ: Higher-High proxy için onceki tick high'lari sakla ===
        self._prev_highs: Dict[str, float] = {}  # sym -> onceki high

    @staticmethod
    def _missing_indicator_fields(values: List[Any]) -> List[str]:
        field_indexes = {
            "rsi": 6,
            "macd": 7,
            "atr": 12,
            "vwap": 13,
            "stoch_k": 14,
            "adx": 15,
            "volume_average": 17,
            "cmf": 18,
        }
        return [name for name, index in field_indexes.items() if len(values) <= index or values[index] is None]

    def fetch_live_market_data(self) -> Dict[str, Any]:
        """
        TradingView scanner API'sinden anlık gerçek NASDAQ, BIST ve KRİPTO borsa fiyatlarını ve indikatörlerini çeker.
        """
        now = time.time()
        if now - self.last_fetch_time < self.cache_ttl_seconds and self.cached_us_data:
            return {**self.cached_us_data, **self.cached_tr_data, **self.cached_crypto_data}

        columns = [
            "name", "close", "change", "high", "low", "volume",
            "RSI", "MACD.macd", "MACD.signal", "EMA20", "EMA50", "EMA200",
            "ATR", "VWAP", "Stoch.K", "ADX", "Volatility.D", "average_volume_10d_calc",
            "ChaikinMoneyFlow",
            "open"   # === YENİ: Candle Body Ratio için açılış fiyatı ===
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        results: Dict[str, Any] = {}

        # Dinamik hedefleri al (LLM/ML/Hacim bazlı seçilmiş aktif varlıklar)
        active_tickers = asset_universe_manager.get_active_tickers()

        # 1. ABD / NASDAQ Verilerini Çek
        try:
            with httpx.Client(timeout=4.0, trust_env=False) as client:
                res_us = client.post(
                    "https://scanner.tradingview.com/america/scan",
                    json={"symbols": {"tickers": active_tickers["NASDAQ"]}, "columns": columns},
                    headers=headers
                )
                if res_us.status_code == 200:
                    data = res_us.json().get("data", [])
                    
                    # Benchmark (QQQ) değişimini bul
                    benchmark_change = 0.0
                    for item in data:
                        if item.get("s", "").endswith(":QQQ"):
                            vals = item.get("d", [])
                            if len(vals) >= 3:
                                benchmark_change = round(float(vals[2] or 0.0), 2)
                            break

                    for item in data:
                        raw_sym = item.get("s", "")
                        clean_sym = raw_sym.split(":")[-1]
                        vals = item.get("d", [])
                        if len(vals) >= 16:
                            price_val = float(vals[1] or 0.0)
                            if price_val <= 0.0:
                                continue
                            price = round(price_val, 2)
                            chg = round(float(vals[2] or 0.0), 2)
                            high = round(float(vals[3] or price), 2)
                            low = round(float(vals[4] or price), 2)
                            vol = float(vals[5] or 0)
                            rsi = round(float(vals[6] or 50.0), 2)
                            macd = round(float(vals[7] or 0.0), 2)
                            ema20 = float(vals[9] or price)
                            ema50 = float(vals[10] or price)
                            ema200 = float(vals[11] or price)
                            atr = float(vals[12] or 1.0)
                            vwap = float(vals[13] or price)
                            stoch_k = round(float(vals[14] or 50.0), 2)
                            adx = round(float(vals[15] or 25.0), 2)
                            vol_avg = float(vals[17] if len(vals) > 17 and vals[17] else vol)
                            vol_ratio = round(vol / vol_avg, 2) if vol_avg > 0 else None
                            cmf = round(float(vals[18] if len(vals) > 18 and vals[18] else 0.0), 3)
                            # === YENİ: Candle open + Higher-High proxy + Bid/Ask proxy ===
                            candle_open_val = round(float(vals[19] if len(vals) > 19 and vals[19] else price), 2)
                            prev_high = self._prev_highs.get(clean_sym, 0.0)
                            self._prev_highs[clean_sym] = high  # Bu tick'in high'ini sakla
                            # Bid/Ask proxy: hacim vs ortalama hacim oranini 0-1 araligina normalize et
                            bid_ask_proxy = round(min(max((vol_ratio or 1.0) / 3.0, 0.0), 1.0), 3) if vol_ratio else 0.5

                            # Supertrend Proxy (Multiplier=3, ATR tabanlı)
                            supertrend_proxy = ((high + low) / 2) - (3 * atr)
                            supertrend_bullish = price > supertrend_proxy

                            results[clean_sym] = {
                                "symbol": clean_sym,
                                "ticker": raw_sym,
                                "market": "NASDAQ",
                                "price": price,
                                "change_pct": chg,
                                "high": high,
                                "low": low,
                                "volume": vol,
                                "rsi": rsi,
                                "macd": macd,
                                "ema_golden_cross": (ema20 > ema50 and ema50 > ema200),
                                "vwap": vwap,
                                "vwap_bullish": price >= vwap,
                                "stoch_k": stoch_k,
                                "adx": adx,
                                "volume_ratio": vol_ratio,
                                "atr_pct": round((atr / price) * 100.0, 2) if price > 0 else 1.5,
                                "cmf": cmf,
                                "rs_score": round(chg - benchmark_change, 2),
                                "supertrend_bullish": supertrend_bullish,
                                # === YENİ ALANLAR ===
                                "candle_open": candle_open_val,
                                "candle_high": high,
                                "candle_low":  low,
                                "prev_high_1": prev_high,
                                "bid_ask_ratio": bid_ask_proxy,
                                "source": "TRADINGVIEW_LIVE_SCANNER",
                                "last_update": time.strftime("%H:%M:%S"),
                                "last_updated_ts": now,
                                "source_timestamp": now,
                                "missing_fields": self._missing_indicator_fields(vals)
                            }

                    # =======================================================
                    # KAZAN-KAZAN: ALPACA HİBRİT GERÇEK ZAMANLI (IEX) OVERRIDE
                    # 15 dakika gecikmeli TV NASDAQ fiyatlarını Alpaca'dan canlı ez.
                    # =======================================================
                    from core.config import settings
                    if getattr(settings, "alpaca_extended_hours", True):
                        try:
                            # Sadece NASDAQ sembollerini çek
                            nasdaq_syms = list(results.keys())
                            if nasdaq_syms:
                                from services.broker.alpaca_bridge import AlpacaBroker
                                # Instantiating is light since it just sets up REST client
                                temp_broker = AlpacaBroker(paper=True)
                                rt_prices = temp_broker.get_realtime_prices(nasdaq_syms)
                                
                                for sym, rt_data in rt_prices.items():
                                    if sym in results:
                                        old_price = results[sym]["price"]
                                        new_price = rt_data["price"]
                                        if new_price > 0:
                                            results[sym]["price"] = new_price
                                            results[sym]["change_pct"] = rt_data["change_pct"]
                                            results[sym]["high"] = rt_data["high"]
                                            results[sym]["low"] = rt_data["low"]
                                            # Update related fields relying on price
                                            if "atr_pct" in results[sym] and "ATR" in columns:
                                                pass # ATR percentage could be updated but it's minor
                                            results[sym]["source"] = "HYBRID_ALPACA_LIVE"
                                            # logger.debug(f"[HYBRID] {sym} fiyatı Alpaca'dan güncellendi: {old_price} -> {new_price}")
                        except Exception as override_err:
                            logger.error(f"[ALPACA OVERRIDE ERROR] {override_err}")
                            
                    self.cached_us_data = results
        except Exception as e:
            logger.warning(f"[TRADINGVIEW LIVE FETCH ERROR - US]: {e}")

        # 2. BIST / Türkiye Verilerini Çek
        try:
            with httpx.Client(timeout=4.0, trust_env=False) as client:
                res_tr = client.post(
                    "https://scanner.tradingview.com/turkey/scan",
                    json={"symbols": {"tickers": active_tickers["BIST"]}, "columns": columns},
                    headers=headers
                )
                if res_tr.status_code == 200:
                    data = res_tr.json().get("data", [])
                    
                    # Benchmark (XU100) değişimini bul
                    benchmark_change = 0.0
                    for item in data:
                        if item.get("s", "").endswith(":XU100"):
                            vals = item.get("d", [])
                            if len(vals) >= 3:
                                benchmark_change = round(float(vals[2] or 0.0), 2)
                            break

                    for item in data:
                        raw_sym = item.get("s", "")
                        clean_sym = raw_sym.split(":")[-1]
                        vals = item.get("d", [])
                        if len(vals) >= 16:
                            price_val = float(vals[1] or 0.0)
                            if price_val <= 0.0:
                                continue
                            price = round(price_val, 2)
                            chg = round(float(vals[2] or 0.0), 2)
                            high = round(float(vals[3] or price), 2)
                            low = round(float(vals[4] or price), 2)
                            vol = float(vals[5] or 0)
                            rsi = round(float(vals[6] or 50.0), 2)
                            macd = round(float(vals[7] or 0.0), 2)
                            ema20 = float(vals[9] or price)
                            ema50 = float(vals[10] or price)
                            ema200 = float(vals[11] or price)
                            atr = float(vals[12] or 1.0)
                            vwap = float(vals[13] or price)
                            stoch_k = round(float(vals[14] or 50.0), 2)
                            adx = round(float(vals[15] or 25.0), 2)
                            vol_avg = float(vals[17] if len(vals) > 17 and vals[17] else vol)
                            vol_ratio = round(vol / vol_avg, 2) if vol_avg > 0 else None
                            cmf = round(float(vals[18] if len(vals) > 18 and vals[18] else 0.0), 3)
                            # === YENİ: Candle open + Higher-High proxy + Bid/Ask proxy ===
                            candle_open_val = round(float(vals[19] if len(vals) > 19 and vals[19] else price), 2)
                            prev_high = self._prev_highs.get(clean_sym, 0.0)
                            self._prev_highs[clean_sym] = high
                            bid_ask_proxy = round(min(max((vol_ratio or 1.0) / 3.0, 0.0), 1.0), 3) if vol_ratio else 0.5

                            # Supertrend Proxy (Multiplier=3, ATR tabanlı)
                            supertrend_proxy = ((high + low) / 2) - (3 * atr)
                            supertrend_bullish = price > supertrend_proxy

                            results[clean_sym] = {
                                "symbol": clean_sym,
                                "ticker": raw_sym,
                                "market": "BIST",
                                "price": price,
                                "change_pct": chg,
                                "high": high,
                                "low": low,
                                "volume": vol,
                                "rsi": rsi,
                                "macd": macd,
                                "ema_golden_cross": (ema20 > ema50 and ema50 > ema200),
                                "vwap": vwap,
                                "vwap_bullish": price >= vwap,
                                "stoch_k": stoch_k,
                                "adx": adx,
                                "volume_ratio": vol_ratio,
                                "atr_pct": round((atr / price) * 100.0, 2) if price > 0 else 1.5,
                                "cmf": cmf,
                                "rs_score": round(chg - benchmark_change, 2),
                                "supertrend_bullish": supertrend_bullish,
                                # === YENİ ALANLAR ===
                                "candle_open": candle_open_val,
                                "candle_high": high,
                                "candle_low":  low,
                                "prev_high_1": prev_high,
                                "bid_ask_ratio": bid_ask_proxy,
                                "source": "TRADINGVIEW_LIVE_SCANNER",
                                "last_update": time.strftime("%H:%M:%S"),
                                "last_updated_ts": now,
                                "source_timestamp": now,
                                "missing_fields": self._missing_indicator_fields(vals)
                            }
                    self.cached_tr_data = {k: v for k, v in results.items() if v["market"] == "BIST"}
        except Exception as e:
            logger.warning(f"[TRADINGVIEW LIVE FETCH ERROR - TR]: {e}")

        # 3. KRİPTO / Crypto Verilerini Çek
        try:
            with httpx.Client(timeout=4.0, trust_env=False) as client:
                res_crypto = client.post(
                    "https://scanner.tradingview.com/crypto/scan",
                    json={"symbols": {"tickers": active_tickers["CRYPTO"]}, "columns": columns},
                    headers=headers
                )
                if res_crypto.status_code == 200:
                    data = res_crypto.json().get("data", [])
                    
                    # Benchmark (BTCUSDT) değişimini bul
                    benchmark_change = 0.0
                    for item in data:
                        if item.get("s", "").endswith(":BTCUSDT"):
                            vals = item.get("d", [])
                            if len(vals) >= 3:
                                benchmark_change = round(float(vals[2] or 0.0), 2)
                            break

                    for item in data:
                        raw_sym = item.get("s", "")
                        clean_sym = raw_sym.split(":")[-1]
                        vals = item.get("d", [])
                        if len(vals) >= 16:
                            price_val = float(vals[1] or 0.0)
                            if price_val <= 0.0:
                                continue
                            price = round(price_val, 4 if price_val < 1.0 else 2)
                            chg = round(float(vals[2] or 0.0), 2)
                            high = round(float(vals[3] or price), 4 if price < 1.0 else 2)
                            low = round(float(vals[4] or price), 4 if price < 1.0 else 2)
                            vol = float(vals[5] or 0)
                            rsi = round(float(vals[6] or 50.0), 2)
                            macd = round(float(vals[7] or 0.0), 2)
                            ema20 = float(vals[9] or price)
                            ema50 = float(vals[10] or price)
                            ema200 = float(vals[11] or price)
                            atr = float(vals[12] or 1.0)
                            vwap = float(vals[13] or price)
                            stoch_k = round(float(vals[14] or 50.0), 2)
                            adx = round(float(vals[15] or 25.0), 2)
                            vol_avg = float(vals[17] if len(vals) > 17 and vals[17] else vol)
                            vol_ratio = round(vol / vol_avg, 2) if vol_avg > 0 else None
                            cmf = round(float(vals[18] if len(vals) > 18 and vals[18] else 0.0), 3)
                            # === YENİ: Candle open + Higher-High proxy + Bid/Ask proxy ===
                            candle_open_val = round(float(vals[19] if len(vals) > 19 and vals[19] else price), 4 if price < 1.0 else 2)
                            prev_high = self._prev_highs.get(clean_sym, 0.0)
                            self._prev_highs[clean_sym] = high
                            bid_ask_proxy = round(min(max((vol_ratio or 1.0) / 3.0, 0.0), 1.0), 3) if vol_ratio else 0.5

                            # Supertrend Proxy (Multiplier=3, ATR tabanlı)
                            supertrend_proxy = ((high + low) / 2) - (3 * atr)
                            supertrend_bullish = price > supertrend_proxy

                            results[clean_sym] = {
                                "symbol": clean_sym,
                                "ticker": raw_sym,
                                "market": "CRYPTO",
                                "price": price,
                                "change_pct": chg,
                                "high": high,
                                "low": low,
                                "volume": vol,
                                "rsi": rsi,
                                "macd": macd,
                                "ema_golden_cross": (ema20 > ema50 and ema50 > ema200),
                                "vwap": vwap,
                                "vwap_bullish": price >= vwap,
                                "stoch_k": stoch_k,
                                "adx": adx,
                                "volume_ratio": vol_ratio,
                                "atr_pct": round((atr / price) * 100.0, 2) if price > 0 else 1.5,
                                "cmf": cmf,
                                "rs_score": round(chg - benchmark_change, 2),
                                "supertrend_bullish": supertrend_bullish,
                                # === YENİ ALANLAR ===
                                "candle_open": candle_open_val,
                                "candle_high": high,
                                "candle_low":  low,
                                "prev_high_1": prev_high,
                                "bid_ask_ratio": bid_ask_proxy,
                                "source": "TRADINGVIEW_LIVE_SCANNER",
                                "last_update": time.strftime("%H:%M:%S"),
                                "last_updated_ts": now,
                                "source_timestamp": now,
                                "missing_fields": self._missing_indicator_fields(vals)
                            }
                    self.cached_crypto_data = {k: v for k, v in results.items() if v["market"] == "CRYPTO"}
        except Exception as e:
            logger.warning(f"[TRADINGVIEW LIVE FETCH ERROR - CRYPTO]: {e}")

        self.last_fetch_time = now
        return results if results else {**self.cached_us_data, **self.cached_tr_data, **self.cached_crypto_data}

tradingview_live_client = TradingViewLiveClient()

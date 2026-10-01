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

        # NASDAQ ve BIST için 15 Dakika (15m), Kripto için 1 Saat (1h)
        columns_15m = [
            "name", "close", "change", "high|15", "low|15", "volume|15",
            "RSI|15", "MACD.macd|15", "MACD.signal|15", "EMA20|15", "EMA50|15", "EMA200|15",
            "ATR|15", "VWAP|15", "Stoch.K|15", "ADX|15", "Volatility.D|15", "average_volume_10d_calc|15",
            "ChaikinMoneyFlow|15", "open|15"
        ]

        columns_60m = [
            "name", "close", "change", "high|60", "low|60", "volume|60",
            "RSI|60", "MACD.macd|60", "MACD.signal|60", "EMA20|60", "EMA50|60", "EMA200|60",
            "ATR|60", "VWAP|60", "Stoch.K|60", "ADX|60", "Volatility.D|60", "average_volume_10d_calc|60",
            "ChaikinMoneyFlow|60", "open|60"
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
            with httpx.Client(timeout=15.0, trust_env=False) as client:
                res_us = client.post(
                    "https://scanner.tradingview.com/america/scan",
                    json={"symbols": {"tickers": active_tickers["NASDAQ"]}, "columns": columns_15m},
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
                            rsi_v = vals[6]; rsi = round(float(rsi_v), 2) if rsi_v is not None else None
                            macd = round(float(vals[7] or 0.0), 2)
                            ema20 = float(vals[9] or price)
                            ema50 = float(vals[10] or price)
                            ema200 = float(vals[11] or price)
                            atr = float(vals[12] or 0.0)
                            vwap = float(vals[13] or price)
                            stoch_v = vals[14]; stoch_k = round(float(stoch_v), 2) if stoch_v is not None else None
                            adx_v = vals[15]; adx = round(float(adx_v), 2) if adx_v is not None else None
                            
                            vol_avg = float(vals[17] if len(vals) > 17 and vals[17] else vol)
                            
                            # YENİ: 15-dakikalık mum kapanış gürültüsünü (Volume Reset) düzeltmek için zaman prorasyonu
                            import time as time_mod
                            from services.risk_engine.market_hours import market_hours_validator
                            
                            status_tuple = market_hours_validator.is_market_open("NASDAQ")
                            is_open = status_tuple[0]
                            session_type = status_tuple[2].get("session", "RTH")
                            
                            # TradingView'in standart hacim verisi sadece Normal Seans (RTH) için güncellenir.
                            # Pre/Post market'te MOC mumunu bölmek sahte hacim patlamaları (5x-10x) yaratır.
                            if is_open and session_type == "RTH":
                                # 15 dakikalık mum için saniye bazlı kusursuz prorasyon
                                candle_start = (int(now) // 900) * 900
                                seconds_in_candle = int(now) - candle_start
                                effective_seconds = max(seconds_in_candle, 60)
                                expected_fraction = effective_seconds / 900.0
                                adjusted_vol_avg = vol_avg * expected_fraction
                                if adjusted_vol_avg > 0:
                                    raw_vol_ratio = vol / adjusted_vol_avg
                                    vol_ratio = round(raw_vol_ratio, 2)
                                else:
                                    vol_ratio = 1.0
                                    
                                    
                                # Sahte hacim kısıtlaması KUSURSUZ İNFAZ PROTOKOLÜ gereği kaldırıldı.
                            else:
                                # Piyasa kapalıyken son mum "Kapanış Müzayedesi (MOC)" mumudur ve 
                                # ortalama bir mumun devasa katı hacme sahiptir.
                                vol_ratio = 1.0
                            
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
                    # from core.config import settings
                    # if getattr(settings, "alpaca_extended_hours", True):
                    #     try:
                    #         nasdaq_syms = list(results.keys())
                    #         if nasdaq_syms:
                    #             from services.broker.alpaca_bridge import AlpacaBroker
                    #             temp_broker = AlpacaBroker(paper=True)
                    #             rt_prices = temp_broker.get_realtime_prices(nasdaq_syms)
                    #             for sym, rt_data in rt_prices.items():
                    #                 if sym in results:
                    #                     new_price = rt_data["price"]
                    #                     if new_price > 0:
                    #                         results[sym]["price"] = new_price
                    #                         results[sym]["change_pct"] = rt_data["change_pct"]
                    #                         results[sym]["high"] = rt_data["high"]
                    #                         results[sym]["low"] = rt_data["low"]
                    #                         results[sym]["source"] = "HYBRID_ALPACA_LIVE"
                    #     except Exception as override_err:
                    #         logger.error(f"[ALPACA OVERRIDE ERROR] {override_err}")
                            
                    self.cached_us_data = results
        except Exception as e:
            logger.warning(f"[TRADINGVIEW LIVE FETCH ERROR - US]: {e}")

        # 2. BIST / Türkiye Verilerini Çek
        try:
            with httpx.Client(timeout=15.0, trust_env=False) as client:
                res_tr = client.post(
                    "https://scanner.tradingview.com/turkey/scan",
                    json={"symbols": {"tickers": active_tickers["BIST"]}, "columns": columns_15m},
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
                            rsi_v = vals[6]; rsi = round(float(rsi_v), 2) if rsi_v is not None else None
                            macd = round(float(vals[7] or 0.0), 2)
                            ema20 = float(vals[9] or price)
                            ema50 = float(vals[10] or price)
                            ema200 = float(vals[11] or price)
                            atr = float(vals[12] or 0.0)
                            vwap = float(vals[13] or price)
                            stoch_v = vals[14]; stoch_k = round(float(stoch_v), 2) if stoch_v is not None else None
                            adx_v = vals[15]; adx = round(float(adx_v), 2) if adx_v is not None else None
                            vol_avg = float(vals[17] if len(vals) > 17 and vals[17] else vol)
                            
                            import time as time_mod
                            from services.risk_engine.market_hours import market_hours_validator
                            
                            status_tuple = market_hours_validator.is_market_open("BIST")
                            is_open = status_tuple[0]
                            session_type = status_tuple[2].get("session", "RTH")
                            
                            if is_open and session_type == "RTH":
                                # 15 dakikalık mum için saniye bazlı kusursuz prorasyon
                                candle_start = (int(now) // 900) * 900
                                seconds_in_candle = int(now) - candle_start
                                effective_seconds = max(seconds_in_candle, 60)
                                expected_fraction = effective_seconds / 900.0
                                adjusted_vol_avg = vol_avg * expected_fraction
                                
                                if adjusted_vol_avg > 0:
                                    raw_vol_ratio = vol / adjusted_vol_avg
                                    vol_ratio = round(raw_vol_ratio, 2)
                                else:
                                    vol_ratio = 1.0
                                    
                                    
                                # Sahte hacim kısıtlaması KUSURSUZ İNFAZ PROTOKOLÜ gereği kaldırıldı.
                            else:
                                vol_ratio = 1.0
                            
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
            with httpx.Client(timeout=15.0, trust_env=False) as client:
                res_crypto = client.post(
                    "https://scanner.tradingview.com/crypto/scan",
                    json={"symbols": {"tickers": active_tickers["CRYPTO"]}, "columns": columns_60m},
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
                            prec = 8 if price_val < 0.0001 else (4 if price_val < 1.0 else 2)
                            price = round(price_val, prec)
                            chg = round(float(vals[2] or 0.0), 2)
                            high = round(float(vals[3] or price), prec)
                            low = round(float(vals[4] or price), prec)
                            vol = float(vals[5] or 0)
                            rsi_v = vals[6]; rsi = round(float(rsi_v), 2) if rsi_v is not None else None
                            macd = round(float(vals[7] or 0.0), 2)
                            ema20 = float(vals[9] or price)
                            ema50 = float(vals[10] or price)
                            ema200 = float(vals[11] or price)
                            atr = float(vals[12] or 0.0)
                            vwap = float(vals[13] or price)
                            stoch_v = vals[14]; stoch_k = round(float(stoch_v), 2) if stoch_v is not None else None
                            adx_v = vals[15]; adx = round(float(adx_v), 2) if adx_v is not None else None
                            adx_v = vals[15]; adx = round(float(adx_v), 2) if adx_v is not None else None
                            vol_avg = float(vals[17] if len(vals) > 17 and vals[17] else vol)
                            
                            # 60 dakikalık mum için saniye bazlı kusursuz prorasyon
                            candle_start = (int(now) // 3600) * 3600
                            seconds_in_candle = int(now) - candle_start
                            # İlk 1 dakikayı 60s gibi say ki sıfıra bölme veya devasa rasyolar çıkmasın
                            effective_seconds = max(seconds_in_candle, 60)
                            expected_fraction = effective_seconds / 3600.0
                            adjusted_vol_avg = vol_avg * expected_fraction
                            
                            raw_vol_ratio = 1.0
                            if adjusted_vol_avg > 0:
                                raw_vol_ratio = vol / adjusted_vol_avg
                                
                            # Sahte hacim kısıtlaması KUSURSUZ İNFAZ PROTOKOLÜ gereği kaldırıldı.

                            vol_ratio = round(raw_vol_ratio, 2)
                            
                            # Aşırı gürültüyü engelle, maks 5.0x
                            vol_ratio = min(vol_ratio, 5.0)
                            
                            cmf = round(float(vals[18] if len(vals) > 18 and vals[18] else 0.0), 3)
                            # === YENİ: Candle open + Higher-High proxy + Bid/Ask proxy ===
                            candle_open_val = round(float(vals[19] if len(vals) > 19 and vals[19] else price), prec)
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

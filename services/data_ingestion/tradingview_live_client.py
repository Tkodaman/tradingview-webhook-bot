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
        
        import httpx
        # Global ve kalıcı bir HTTP istemcisi (Connection limit & DNS timeout hatalarını engeller)
        self.http_client = httpx.Client(timeout=20.0, trust_env=False)

    def _parse_mtf_row(self, clean_sym: str, raw_sym: str, market: str, vals: List[Any], now: float, is_rth: bool, benchmark_change: float) -> Optional[Dict[str, Any]]:
        import time
        if len(vals) < 37: return None
        price_val = float(vals[1] or 0.0)
        if price_val <= 0.0: return None
        prec = 8 if price_val < 0.0001 else (4 if price_val < 1.0 else 2)
        price = round(price_val, prec)
        chg = round(float(vals[2] or 0.0), 2)
        
        high_15, low_15 = round(float(vals[3] or price), prec), round(float(vals[4] or price), prec)
        vol_15 = float(vals[5] or 0)
        rsi_15_v = vals[6]; rsi_15 = float(rsi_15_v) if rsi_15_v is not None else 50.0
        macd_15 = float(vals[7] or 0.0)
        ema20_15, ema50_15, ema200_15 = float(vals[9] or price), float(vals[10] or price), float(vals[11] or price)
        atr_15, vwap_15 = float(vals[12] or 0.0), float(vals[13] or price)
        stoch_15 = vals[14]; stoch_k_15 = float(stoch_15) if stoch_15 is not None else 50.0
        adx_15 = vals[15]; adx_15_val = float(adx_15) if adx_15 is not None else 20.0
        vol_avg_15 = float(vals[17] if len(vals) > 17 and vals[17] else vol_15)
        cmf_15 = float(vals[18] if len(vals) > 18 and vals[18] else 0.0)
        # Yeni Eklenen Elite Sentinel Kolonları (15m)
        bb_upper_15 = float(vals[20] if len(vals) > 20 and vals[20] else price)
        bb_lower_15 = float(vals[21] if len(vals) > 21 and vals[21] else price)
        cci_15 = float(vals[22] if len(vals) > 22 and vals[22] else 0.0)
        pivot_s1_15 = float(vals[23] if len(vals) > 23 and vals[23] else 0.0)
        
        # 60m Dilimi (Önceden index 20'den başlıyordu, şimdi 24'ten başlıyor)
        high_60, low_60 = round(float(vals[24] if len(vals) > 24 and vals[24] else price), prec), round(float(vals[25] if len(vals) > 25 and vals[25] else price), prec)
        vol_60 = float(vals[26] if len(vals) > 26 and vals[26] else 0)
        rsi_60_v = vals[27] if len(vals) > 27 else None; rsi_60 = float(rsi_60_v) if rsi_60_v is not None else 50.0
        macd_60 = float(vals[28] if len(vals) > 28 and vals[28] else 0.0)
        ema20_60, ema50_60, ema200_60 = float(vals[30] if len(vals) > 30 and vals[30] else price), float(vals[31] if len(vals) > 31 and vals[31] else price), float(vals[32] if len(vals) > 32 and vals[32] else price)
        atr_60 = float(vals[33] if len(vals) > 33 and vals[33] else 0.0)
        stoch_60 = vals[35] if len(vals) > 35 else None; stoch_k_60 = float(stoch_60) if stoch_60 is not None else 50.0
        adx_60 = vals[36] if len(vals) > 36 else None; adx_60_val = float(adx_60) if adx_60 is not None else 20.0
        vol_avg_60 = float(vals[38] if len(vals) > 38 and vals[38] else vol_60)
        cmf_60 = float(vals[39] if len(vals) > 39 and vals[39] else 0.0)
        open_60 = round(float(vals[40] if len(vals) > 40 and vals[40] else price), prec)
        
        # Yeni Eklenen Elite Sentinel Kolonları (60m)
        bb_upper_60 = float(vals[41] if len(vals) > 41 and vals[41] else price)
        bb_lower_60 = float(vals[42] if len(vals) > 42 and vals[42] else price)
        cci_60 = float(vals[43] if len(vals) > 43 and vals[43] else 0.0)
        pivot_s1_60 = float(vals[44] if len(vals) > 44 and vals[44] else 0.0)

        rsi_blended = round((rsi_15 * 0.4) + (rsi_60 * 0.6), 2)
        macd_blended = round((macd_15 * 0.4) + (macd_60 * 0.6), 2)
        stoch_k_blended = round((stoch_k_15 * 0.4) + (stoch_k_60 * 0.6), 2)
        adx_blended = round((adx_15_val * 0.4) + (adx_60_val * 0.6), 2)
        cmf_blended = round((cmf_15 * 0.4) + (cmf_60 * 0.6), 3)
        atr_blended = (atr_15 * 0.4) + (atr_60 * 0.6)
        ema_golden_cross = (ema20_15 > ema50_15 and ema50_15 > ema200_15) or (ema20_60 > ema50_60 and ema50_60 > ema200_60)
        
        # Elite Sentinel Blends
        cci_blended = round((cci_15 * 0.4) + (cci_60 * 0.6), 2)
        bb_width_blended = round((((bb_upper_15 - bb_lower_15) / price) * 0.4) + (((bb_upper_60 - bb_lower_60) / price) * 0.6), 4) if price > 0 else 0
        pivot_dist = abs(price - pivot_s1_15) / price if price > 0 else 1.0
        bb_dist = abs(price - bb_lower_15) / price if price > 0 else 1.0
        lux_support_dist = round(min(pivot_dist, bb_dist), 4)

        candle_start_15 = (int(now) // 900) * 900
        seconds_in_candle_15 = int(now) - candle_start_15
        effective_seconds_15 = max(seconds_in_candle_15, 30)
        if market != "CRYPTO" and not is_rth: vol_ratio_15 = 1.0
        else:
            adj_vol_avg_15 = vol_avg_15 * (effective_seconds_15 / 900.0)
            raw_vr_15 = vol_15 / adj_vol_avg_15 if adj_vol_avg_15 > 0 else 1.0
            if seconds_in_candle_15 < 300:
                df = (300 - seconds_in_candle_15) / 300.0
                raw_vr_15 = (raw_vr_15 * (1 - df)) + (1.0 * df)
            vol_ratio_15 = raw_vr_15

        candle_start_60 = (int(now) // 3600) * 3600
        seconds_in_candle_60 = int(now) - candle_start_60
        effective_seconds_60 = max(seconds_in_candle_60, 60)
        if market != "CRYPTO" and not is_rth: vol_ratio_60 = 1.0
        else:
            adj_vol_avg_60 = vol_avg_60 * (effective_seconds_60 / 3600.0)
            raw_vr_60 = vol_60 / adj_vol_avg_60 if adj_vol_avg_60 > 0 else 1.0
            if seconds_in_candle_60 < 900:
                df = (900 - seconds_in_candle_60) / 900.0
                raw_vr_60 = (raw_vr_60 * (1 - df)) + (1.0 * df)
            vol_ratio_60 = raw_vr_60

        vol_ratio_blended = round((vol_ratio_15 * 0.4) + (vol_ratio_60 * 0.6), 2)
        vol_ratio_blended = min(vol_ratio_blended, 5.0)

        prev_high = self._prev_highs.get(clean_sym, 0.0)
        self._prev_highs[clean_sym] = high_60

        bid_ask_proxy = round(min(max((vol_ratio_blended or 1.0) / 3.0, 0.0), 1.0), 3)

        supertrend_proxy = ((high_60 + low_60) / 2) - (3 * atr_blended)
        supertrend_bullish = price > supertrend_proxy

        return {
            "symbol": clean_sym,
            "ticker": raw_sym,
            "market": market,
            "price": price,
            "change_pct": chg,
            "high": high_60,
            "low": low_60,
            "volume": vol_15,
            "rsi": rsi_blended,
            "macd": macd_blended,
            "ema_golden_cross": ema_golden_cross,
            "vwap": vwap_15,
            "vwap_bullish": price >= vwap_15,
            "stoch_k": stoch_k_blended,
            "adx": adx_blended,
            "volume_ratio": vol_ratio_blended,
            "atr_pct": round((atr_blended / price) * 100.0, 2) if price > 0 else 1.5,
            "cmf": cmf_blended,
            "rs_score": round(chg - benchmark_change, 2),
            "supertrend_bullish": supertrend_bullish,
            "candle_open": open_60,
            "candle_high": high_60,
            "candle_low":  low_60,
            "prev_high_1": prev_high,
            "bid_ask_ratio": bid_ask_proxy,
            "cci": cci_blended,
            "bb_width": bb_width_blended,
            "lux_support_dist": lux_support_dist,
            "source": "TRADINGVIEW_LIVE_SCANNER",
            "last_update": time.strftime("%H:%M:%S"),
            "last_updated_ts": now,
            "missing_fields": self._missing_indicator_fields(vals)
        }

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
        import time
        now = time.time()
        if now - self.last_fetch_time < self.cache_ttl_seconds and self.cached_us_data:
            return {**self.cached_us_data, **self.cached_tr_data, **self.cached_crypto_data}

        # MTF Ortalama (15m + 1h + 2h). Elite Sentinel Proxy verileri eklendi (BB, CCI, Pivot)
        columns_mtf = [
            "name", "close", "change", 
            "high|15", "low|15", "volume", "RSI|15", "MACD.macd|15", "MACD.signal|15", "EMA20|15", "EMA50|15", "EMA200|15", "ATR|15", "VWAP|15", "Stoch.K|15", "ADX|15", "Volatility.D|15", "average_volume_10d_calc", "ChaikinMoneyFlow|15", "open|15", "BB.upper|15", "BB.lower|15", "CCI20|15", "Pivot.M.Classic.S1|15",
            "high|60", "low|60", "volume|60", "RSI|60", "MACD.macd|60", "MACD.signal|60", "EMA20|60", "EMA50|60", "EMA200|60", "ATR|60", "VWAP|60", "Stoch.K|60", "ADX|60", "Volatility.D|60", "average_volume_10d_calc|60", "ChaikinMoneyFlow|60", "open|60", "BB.upper|60", "BB.lower|60", "CCI20|60", "Pivot.M.Classic.S1|60",
            "high|120", "low|120", "volume|120", "RSI|120", "MACD.macd|120", "MACD.signal|120", "EMA20|120", "EMA50|120", "EMA200|120", "ATR|120", "VWAP|120", "Stoch.K|120", "ADX|120", "Volatility.D|120", "average_volume_10d_calc|120", "ChaikinMoneyFlow|120", "open|120", "BB.upper|120", "BB.lower|120", "CCI20|120", "Pivot.M.Classic.S1|120"
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
            
                res_us = self.http_client.post(
                    "https://scanner.tradingview.com/america/scan",
                    json={"symbols": {"tickers": active_tickers["NASDAQ"]}, "columns": columns_mtf},
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
                            
                            # MTF Hacim ve RSI Çıkarımı
                            vol_15 = float(vals[5] or 0)
                            rsi_15_v = vals[6]; rsi_15 = float(rsi_15_v) if rsi_15_v is not None else 50.0
                            
                            vol_60 = float(vals[26] or 0) if len(vals) > 26 else vol_15
                            rsi_60_v = vals[27] if len(vals) > 27 else None; rsi_60 = float(rsi_60_v) if rsi_60_v is not None else rsi_15
                            
                            vol_120 = float(vals[47] or 0) if len(vals) > 47 else vol_60
                            rsi_120_v = vals[48] if len(vals) > 48 else None; rsi_120 = float(rsi_120_v) if rsi_120_v is not None else rsi_60
                            
                            vol = vol_15 # Uyumluluk için
                            
                            macd = round(float(vals[7] or 0.0), 2)
                            ema20 = float(vals[9] or price)
                            ema50 = float(vals[10] or price)
                            ema200 = float(vals[11] or price)
                            atr = float(vals[12] or 0.0)
                            vwap = float(vals[13] or price)
                            stoch_v = vals[14]; stoch_k = round(float(stoch_v), 2) if stoch_v is not None else None
                            adx_v = vals[15]; adx = round(float(adx_v), 2) if adx_v is not None else None
                            
                            vol_avg = float(vals[17] if len(vals) > 17 and vals[17] else vol_15)
                            
                            import time as time_mod
                            from services.risk_engine.market_hours import market_hours_validator
                            
                            status_tuple = market_hours_validator.is_market_open("NASDAQ")
                            is_open = status_tuple[0]
                            session_type = status_tuple[2].get("session", "RTH")
                            
                            if is_open and session_type == "RTH":
                                import datetime
                                # Bugünün açılışından (ör: 09:30) beri kaç dakika geçtiğini hesapla
                                now_utc = datetime.datetime.utcnow()
                                
                                # ABD Piyasası (NASDAQ) hesabı için basit bir proxy: 
                                # 6.5 saat = 390 dakika. Biz güncel olarak geçen dakikayı bulmalıyız.
                                # Veya daha basiti, Tradingview'in doğrudan kümülatif gün hacmini beklenen orana göre hesaplamak.
                                # Piyasa genelde UTC 14:30 - 21:00 arasıdır (6.5 saat)
                                elapsed_minutes = (now_utc.hour * 60 + now_utc.minute) - (14 * 60 + 30)
                                elapsed_minutes = max(15, min(390, elapsed_minutes)) # En az 15dk, en çok 390dk
                                
                                # Günlük beklenen hacim (O ana kadar ki)
                                expected_cumulative_vol = vol_avg * (elapsed_minutes / 390.0)
                                vol_ratio = round(vol / expected_cumulative_vol, 2) if expected_cumulative_vol > 0 else 1.0
                                
                                if vol_ratio >= 2.5:
                                    try:
                                        from services.engine.bot_thought_stream import bot_thought_stream
                                        def _fvol(v): return f"{v/1000000:.1f}M" if v >= 1000000 else f"{v/1000:.1f}K"
                                        msg = f"Bugün seans açılalı {int(elapsed_minutes)} dk oldu. Normalde {clean_sym} için {_fvol(expected_cumulative_vol)} hacim olması lazımdı, ama şu an {_fvol(vol)} var! Demek ki devasa bir kurumsal alım ({vol_ratio}x Patlama) var."
                                        bot_thought_stream.add_throttled(
                                            category="🔥 HACİM RADARI", 
                                            symbol=clean_sym, 
                                            message=msg, 
                                            level="INFO", 
                                            cooldown_sec=43200
                                        )
                                    except Exception:
                                        pass
                            else:
                                vol_ratio = 1.0
                                
                            # Harmanlanmış (Blended) RSI (%30 15d + %35 60d + %35 120d)
                            rsi = round((rsi_15 * 0.30) + (rsi_60 * 0.35) + (rsi_120 * 0.35), 2)
                            
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
                    try:
                        nasdaq_syms = list(results.keys())
                        if nasdaq_syms:
                            from services.broker.factory import get_broker
                            temp_broker = get_broker('alpaca', paper=True)
                            rt_prices = temp_broker.get_realtime_prices(nasdaq_syms)
                            if rt_prices:
                                for sym, rt_data in rt_prices.items():
                                    if sym in results:
                                        new_price = rt_data.get("price", 0.0)
                                        if new_price > 0:
                                            results[sym]["price"] = new_price
                                            results[sym]["change_pct"] = rt_data.get("change_pct", results[sym]["change_pct"])
                                            
                                            # Update high/low only if Alpaca provides them and they are valid
                                            if rt_data.get("high") and rt_data["high"] > 0:
                                                results[sym]["high"] = rt_data["high"]
                                            if rt_data.get("low") and rt_data["low"] > 0:
                                                results[sym]["low"] = rt_data["low"]
                                                
                                            results[sym]["source"] = "HYBRID_ALPACA_LIVE"
                                            # Override timestamp since it's real-time now
                                            results[sym]["last_updated_ts"] = time.time()
                    except Exception as override_err:
                        import traceback
                        logger.error(f"[ALPACA OVERRIDE ERROR] {override_err}\n{traceback.format_exc()}")
                            
                    self.cached_us_data = results
                elif res_us.status_code == 429:
                    logger.warning("[TRADINGVIEW RATE LIMIT] 429 Too Many Requests (US). Dinlenmeye geçiliyor...")
                    self.last_fetch_time = time.time() + 15.0
                    return {**self.cached_us_data, **self.cached_tr_data, **self.cached_crypto_data}
        except Exception as e:
            logger.warning(f"[TRADINGVIEW LIVE FETCH ERROR - US]: {e}")

        # 2. BIST / Türkiye Verilerini Çek
        try:
            
                res_tr = self.http_client.post(
                    "https://scanner.tradingview.com/turkey/scan",
                    json={"symbols": {"tickers": active_tickers["BIST"]}, "columns": columns_mtf},
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
                            
                            # MTF Hacim ve RSI Çıkarımı
                            vol_15 = float(vals[5] or 0)
                            rsi_15_v = vals[6]; rsi_15 = float(rsi_15_v) if rsi_15_v is not None else 50.0
                            
                            vol_60 = float(vals[26] or 0) if len(vals) > 26 else vol_15
                            rsi_60_v = vals[27] if len(vals) > 27 else None; rsi_60 = float(rsi_60_v) if rsi_60_v is not None else rsi_15
                            
                            vol_120 = float(vals[47] or 0) if len(vals) > 47 else vol_60
                            rsi_120_v = vals[48] if len(vals) > 48 else None; rsi_120 = float(rsi_120_v) if rsi_120_v is not None else rsi_60
                            
                            vol = vol_15 # Uyumluluk için
                            
                            macd = round(float(vals[7] or 0.0), 2)
                            ema20 = float(vals[9] or price)
                            ema50 = float(vals[10] or price)
                            ema200 = float(vals[11] or price)
                            atr = float(vals[12] or 0.0)
                            vwap = float(vals[13] or price)
                            stoch_v = vals[14]; stoch_k = round(float(stoch_v), 2) if stoch_v is not None else None
                            adx_v = vals[15]; adx = round(float(adx_v), 2) if adx_v is not None else None
                            vol_avg = float(vals[17] if len(vals) > 17 and vals[17] else vol_15)
                            
                            import time as time_mod
                            from services.risk_engine.market_hours import market_hours_validator
                            
                            status_tuple = market_hours_validator.is_market_open("BIST")
                            is_open = status_tuple[0]
                            session_type = status_tuple[2].get("session", "RTH")
                            
                            if is_open and session_type == "RTH":
                                import datetime
                                now_utc = datetime.datetime.utcnow()
                                
                                # BIST UTC 07:00 - 15:00 arasıdır (8 saat = 480 dakika)
                                elapsed_minutes = (now_utc.hour * 60 + now_utc.minute) - (7 * 60 + 0)
                                elapsed_minutes = max(15, min(480, elapsed_minutes)) # En az 15dk, en çok 480dk
                                
                                # Günlük beklenen hacim (O ana kadar ki)
                                expected_cumulative_vol = vol_avg * (elapsed_minutes / 480.0)
                                vol_ratio = round(vol / expected_cumulative_vol, 2) if expected_cumulative_vol > 0 else 1.0
                                
                                if vol_ratio >= 2.5:
                                    try:
                                        from services.engine.bot_thought_stream import bot_thought_stream
                                        def _fvol(v): return f"{v/1000000:.1f}M" if v >= 1000000 else f"{v/1000:.1f}K"
                                        msg = f"Bugün seans açılalı {int(elapsed_minutes)} dk oldu. Normalde {clean_sym} için {_fvol(expected_cumulative_vol)} lot hacim olmalıydı, ama piyasada şu an {_fvol(vol)} lot var! Demek ki devasa bir kurumsal alım ({vol_ratio}x Patlama) var."
                                        bot_thought_stream.add_throttled(
                                            category="🔥 HACİM RADARI", 
                                            symbol=clean_sym, 
                                            message=msg, 
                                            level="INFO", 
                                            cooldown_sec=43200
                                        )
                                    except Exception:
                                        pass
                            else:
                                vol_ratio = 1.0
                                
                            rsi = round((rsi_15 * 0.30) + (rsi_60 * 0.35) + (rsi_120 * 0.35), 2)
                            
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
                elif res_tr.status_code == 429:
                    logger.warning("[TRADINGVIEW RATE LIMIT] 429 Too Many Requests (BIST).")
                    self.last_fetch_time = time.time() + 15.0
        except Exception as e:
            logger.warning(f"[TRADINGVIEW LIVE FETCH ERROR - TR]: {e}")

        # 3. KRİPTO / Crypto Verilerini Çek
        try:
            
                res_crypto = self.http_client.post(
                    "https://scanner.tradingview.com/crypto/scan",
                    json={"symbols": {"tickers": active_tickers["CRYPTO"]}, "columns": columns_mtf},
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
                        
                        # KÖKTEN ÇÖZÜM: Shitcoin ve Stablecoin Çiftlerini Filtrele (HYPERFDUSD, USDC vb.)
                        if clean_sym.endswith("FDUSD") or clean_sym.endswith("USDC") or clean_sym.endswith("TUSD") or clean_sym.endswith("BUSD") or clean_sym.endswith("EUR"):
                            continue
                        if not (clean_sym.endswith("USDT") or clean_sym.endswith("TRY")):
                            continue
                        if clean_sym in ["USDCUSDT", "TUSDUSDT", "FDUSDUSDT", "BUSDUSDT", "EURUSDT", "TRYUSDT", "PAXGUSDT"]:
                            continue
                            
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
                            
                            # MTF Hacim ve RSI Çıkarımı
                            vol_15 = float(vals[5] or 0)
                            rsi_15_v = vals[6]; rsi_15 = float(rsi_15_v) if rsi_15_v is not None else 50.0
                            
                            vol_60 = float(vals[26] or 0) if len(vals) > 26 else vol_15
                            rsi_60_v = vals[27] if len(vals) > 27 else None; rsi_60 = float(rsi_60_v) if rsi_60_v is not None else rsi_15
                            
                            vol = vol_15 # Uyumluluk
                            
                            macd = round(float(vals[7] or 0.0), 2)
                            ema20 = float(vals[9] or price)
                            ema50 = float(vals[10] or price)
                            ema200 = float(vals[11] or price)
                            atr = float(vals[12] or 0.0)
                            vwap = float(vals[13] or price)
                            stoch_v = vals[14]; stoch_k = round(float(stoch_v), 2) if stoch_v is not None else None
                            adx_v = vals[15]; adx = round(float(adx_v), 2) if adx_v is not None else None
                            vol_avg = float(vals[17] if len(vals) > 17 and vals[17] else vol_15)
                            
                            import datetime
                            now_utc = datetime.datetime.utcnow()
                            
                            # Kripto günde 24 saat açıktır (1440 dakika)
                            elapsed_minutes = (now_utc.hour * 60 + now_utc.minute)
                            elapsed_minutes = max(15, elapsed_minutes) # Gün başında 0'a bölme hatası olmasın diye en az 15dk
                            
                            # Günlük beklenen hacim (O ana kadar ki kümülatif)
                            expected_cumulative_vol = vol_avg * (elapsed_minutes / 1440.0)
                            vol_ratio = round(vol / expected_cumulative_vol, 2) if expected_cumulative_vol > 0 else 1.0
                            
                            # +2 Adım Doktrini: Gerçek Binance X-Ray Verisini Çek (Proxy kullanma!)
                            # Hacim 1.25'i geçerse yarışta (sıralamada) etkili olsun diye X-Ray'i çekeriz.
                            xray_ratio = None
                            buy_vol_str = "Bilinmiyor"
                            sell_vol_str = "Bilinmiyor"
                            
                            if vol_ratio >= 1.25:
                                try:
                                    import requests
                                    import traceback
                                    import time
                                    import random
                                    
                                    if not hasattr(self, '_req_session'):
                                        self._req_session = requests.Session()
                                        
                                    if not hasattr(self, '_xray_ratios'):
                                        self._xray_ratios = {}
                                    if not hasattr(self, '_xray_last_fetch'):
                                        self._xray_last_fetch = {}
                                        
                                    now_ts = time.time()
                                    # Tereyağından kıl çeker gibi: Connection Pooling (Session) ile 15 saniyede bir çekilir, anlıktır.
                                    if clean_sym not in self._xray_last_fetch or (now_ts - self._xray_last_fetch.get(clean_sym, 0)) > 15:
                                        import json, os
                                        # --- ŞALTER 1: GÖRÜNMEZ WSS KALKANI (SIFIR API) ---
                                        wss_cache_path = os.path.join(os.path.dirname(__file__), "wss_xray_cache.json")
                                        wss_data = {}
                                        try:
                                            if os.path.exists(wss_cache_path):
                                                with open(wss_cache_path, "r") as f:
                                                    wss_data = json.load(f)
                                        except Exception:
                                            pass
                                            
                                        taker_buy_vol = 0.0
                                        taker_sell_vol = 0.0
                                        
                                        if clean_sym in wss_data and (now_ts - wss_data[clean_sym].get("ts", 0)) < 900:
                                            # WSS Cache'ten başarıyla okundu
                                            xray_ratio = wss_data[clean_sym]["xray_ratio"]
                                            taker_buy_vol = wss_data[clean_sym].get("taker_buy", 0)
                                            taker_sell_vol = wss_data[clean_sym].get("taker_sell", 0)
                                            self._xray_ratios[clean_sym] = xray_ratio
                                            self._xray_last_fetch[clean_sym] = now_ts
                                        else:
                                            # --- ŞALTER 2 & 3: REST API (PROXY KORUMALI / ROUND-ROBIN) ---
                                            endpoints = ["api.binance.com", "api1.binance.com", "api2.binance.com", "api3.binance.com"]
                                            api_host = random.choice(endpoints)
                                            proxies = None
                                            proxy_url = os.getenv("BINANCE_PROXY")
                                            if proxy_url:
                                                proxies = {"http": proxy_url, "https": proxy_url}
                                            
                                            try:
                                                # USER REQUEST: Kümülatif 15m, 30m, 45m ortalaması (Smooth/Stabil XR)
                                                resp = self._req_session.get(f"https://{api_host}/api/v3/klines?symbol={clean_sym}&interval=15m&limit=3", proxies=proxies, timeout=5)
                                                if resp.status_code == 200:
                                                    klines = resp.json()
                                                    total_vol = sum([float(k[5]) for k in klines])
                                                    taker_buy_vol = sum([float(k[9]) for k in klines])
                                                    taker_sell_vol = total_vol - taker_buy_vol
                                                    
                                                    if taker_sell_vol > 0:
                                                        xray_ratio = round(taker_buy_vol / taker_sell_vol, 2)
                                                    else:
                                                        xray_ratio = 9.99
                                                        
                                                    self._xray_ratios[clean_sym] = xray_ratio
                                                    self._xray_last_fetch[clean_sym] = now_ts
                                                else:
                                                    logger.error(f"[ŞALTER 3] {clean_sym} Hata Kodu: {resp.status_code}")
                                            except Exception as e:
                                                logger.error(f"[ŞALTER 3] REST/Proxy Hatası: {e}")
                                                
                                        def _fvol2(v): return f"{v/1000000:.1f}M" if v >= 1000000 else f"{v/1000:.1f}K"
                                        buy_vol_str = _fvol2(taker_buy_vol)
                                        sell_vol_str = _fvol2(taker_sell_vol)
                                        
                                        # Eğer hala bulunamadıysa (Tüm şalterler kapalıysa)
                                        if clean_sym not in self._xray_ratios:
                                            xray_ratio = self._xray_ratios.get(clean_sym, -1.0)
                                    else:
                                        # Önbellekteki (max 15 saniyelik) taze veriyi kullan
                                        xray_ratio = self._xray_ratios.get(clean_sym, -1.0)
                                        
                                except Exception as e:
                                    import traceback
                                    logger.error(f"[X-Ray Hata] {clean_sym} API çekilemedi: {e}")
                                    xray_ratio = self._xray_ratios.get(clean_sym, -1.0)
                                    import traceback
                                    logger.error(f"[X-Ray Hata] {clean_sym} API çekilemedi: {e}\n{traceback.format_exc()}")

                            # Eskiden sadece 2.5'te çekiyordu, şimdi 2.5'te sadece Telegram Radarı öter.
                            if vol_ratio >= 2.5 and xray_ratio is not None:
                                try:
                                    from services.engine.bot_thought_stream import bot_thought_stream
                                    from services.engine.telegram_notifier import send_telegram_alert_throttled
                                    
                                    def _fvol(v): return f"{v/1000000:.1f}M" if v >= 1000000 else f"{v/1000:.1f}K"
                                    
                                    if xray_ratio >= 1.5:
                                        ai_thought = "🧠 <b>[Otonom Yargı]:</b> Devasa hacim ve net TAKER BUY (Alıcı) üstünlüğü var. Kurumsal (balina) para fiyata yukarı yönlü basıyor. Momentuma dahil olmak nispeten güvenli."
                                        tel_badge = f"🟢 [X-Ray Ratio: {xray_ratio} (GÜÇLÜ ALIM, GÜVENLİ)]\nMarket Alım (Taker Buy): {buy_vol_str}\nMarket Satım (Taker Sell): {sell_vol_str}"
                                    elif xray_ratio >= 1.0:
                                        ai_thought = "🧠 <b>[Otonom Yargı]:</b> Hacim artışı alıcılarla destekleniyor. Para girişi var ancak agresif balina baskısı henüz yok. Kırılım yakından izlenmeli."
                                        tel_badge = f"🟢 [X-Ray Ratio: {xray_ratio} (POZİTİF ALIM)]\nMarket Alım (Taker Buy): {buy_vol_str}\nMarket Satım (Taker Sell): {sell_vol_str}"
                                    elif xray_ratio >= 0.75:
                                        ai_thought = "🧠 <b>[Otonom Yargı]:</b> <b>DİKKAT!</b> Hacim var ama ağırlıklı satıcılardan (Taker Sell) geliyor. Biri fiyatı yeşil gösterip gizlice mal dağıtıyor olabilir (Dağıtım Evresi)."
                                        tel_badge = f"🟠 [X-Ray Ratio: {xray_ratio} (ZAYIF, MAL DAĞITIMI ŞÜPHESİ)]\nMarket Alım (Taker Buy): {buy_vol_str}\nMarket Satım (Taker Sell): {sell_vol_str}"
                                    else:
                                        ai_thought = "🧠 <b>[Otonom Yargı]:</b> <b>ÖLÜMCÜL TUZAK!</b> Hacim devasa ama agresif Satıcı (Taker Sell) baskın. Balinalar FOMO'ya kapılanlara tepeden mal boşaltıyor. KESİNLİKLE UZAK DUR!"
                                        tel_badge = f"🔴 [X-Ray Ratio: {xray_ratio} (TUZAK / AĞIR MAL BOŞALTMA!)]\nMarket Alım (Taker Buy): {buy_vol_str}\nMarket Satım (Taker Sell): {sell_vol_str}"

                                    xray_badge = f"<b>[X-Ray Ratio: {xray_ratio}]</b>\nMarket Alım: {buy_vol_str} | Market Satım: {sell_vol_str}"
                                        
                                    html_msg = f"Normalde {clean_sym} için {_fvol(expected_cumulative_vol)} hacim beklenirken, {_fvol(vol)} hacim var ({vol_ratio}x Patlama)!\n{xray_badge}\n\n{ai_thought}"
                                    tel_msg = f"⚡ 🔥 <b>HACİM PATLAMASI ({vol_ratio}x) | {clean_sym}</b>\n\n<b>Normal Hacim:</b> {_fvol(expected_cumulative_vol)}\n<b>Şu anki Hacim:</b> {_fvol(vol)}\n\n{tel_badge}\n\n{ai_thought}"
                                    
                                    # Dashboard için HTML bildirim
                                    bot_thought_stream.add_throttled(
                                        category="🔥 HACİM RADARI", 
                                        symbol=clean_sym, 
                                        message=html_msg, 
                                        level="INFO", 
                                        cooldown_sec=43200
                                    )
                                    # Telegram'a da doğrudan uyarı gönder (12 saat cooldown ile)
                                    send_telegram_alert_throttled(tel_msg, throttle_key=f"VOL_RADAR_{clean_sym}", cooldown_sec=43200)
                                    
                                    # 🚀 [KONSEY / OTONOM OVERRIDE - KADERİNE TERK ETME!]
                                    # Eğer balina boşaltması (Tuzak) varsa ve elimizde bu varlık (Manuel dahi olsa) açıksa Otonom ipleri ele alır!
                                    if xray_ratio < 0.75:
                                        try:
                                            from services.engine.live_trade_manager import live_trade_manager
                                            for pid, pos in live_trade_manager.positions.items():
                                                if pos.symbol == clean_sym and pos.status in ["OPEN", "SHADOW_OPEN"]:
                                                    logger.warning(f"🚨 [OTONOM DİZGİNLERİ ELE ALDI] {clean_sym} Ölümcül Tuzak! Manuel pozisyon dahi olsa müdahale ediliyor!")
                                                    
                                                    # Güncel fiyatı al (kârda mıyız zararda mı?)
                                                    curr_price = float(vals[1] if isinstance(vals, list) and len(vals) > 1 else pos.current_price)
                                                    
                                                    # Eğer pozisyon kârdaysa, tereddüt etmeden zirvede kârı al ve ÇIK.
                                                    if (pos.side == "BUY" and curr_price > pos.entry_price) or (pos.side == "SELL" and curr_price < pos.entry_price):
                                                        live_trade_manager.close_position(pid, "CLOSED_SMART_MONEY_DUMP")
                                                        tel_msg_exit = f"🚨 <b>ACİL ÇIKIŞ (OTONOM YARGI)</b> 🚨\n{clean_sym} Balina boşaltması tespit edildi! Otonom risk yönetimi dizginleri ele aldı ve mevcut pozisyon zirve kârdan kapatıldı (Golden Lock)!"
                                                        send_telegram_alert_throttled(tel_msg_exit, throttle_key=f"EMERGENCY_{clean_sym}", cooldown_sec=60)
                                                    else:
                                                        # Zarardaysa SL'i acımasızca giriş fiyatına çok yakın bir yere (Max %0.5 zarar) sıkılaştır!
                                                        new_sl = round(pos.entry_price * 0.995, 8) if pos.side == "BUY" else round(pos.entry_price * 1.005, 8)
                                                        if pos.side == "BUY" and new_sl > pos.stop_loss_price:
                                                            pos.stop_loss_price = new_sl
                                                            pos.trailing_stop_activated = True
                                                        elif pos.side == "SELL" and new_sl < pos.stop_loss_price:
                                                            pos.stop_loss_price = new_sl
                                                            pos.trailing_stop_activated = True
                                                        live_trade_manager.save_state()
                                        except Exception as e:
                                            logger.error(f"[Otonom Override Hatası] {e}")
                                            
                                except Exception:
                                    pass
                            
                            rsi = round((rsi_15 * 0.40) + (rsi_60 * 0.60), 2)
                            
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
                                "xray_ratio": getattr(self, '_xray_ratios', {}).get(clean_sym, None),
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
                elif res_crypto.status_code == 429:
                    logger.warning("[TRADINGVIEW RATE LIMIT] 429 Too Many Requests (CRYPTO).")
                    self.last_fetch_time = time.time() + 15.0
        except Exception as e:
            logger.warning(f"[TRADINGVIEW LIVE FETCH ERROR - CRYPTO]: {e}")

        self.last_fetch_time = now
        return results if results else {**self.cached_us_data, **self.cached_tr_data, **self.cached_crypto_data}

tradingview_live_client = TradingViewLiveClient()

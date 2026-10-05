import re
import sys

filepath = r"C:\Users\ASUS\OneDrive\Desktop\tradingview-webhook-bot\services\data_ingestion\tradingview_live_client.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace columns
old_columns = """        # NASDAQ ve BIST için 15 Dakika (15m), Kripto için 1 Saat (1h)
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
        ]"""
new_columns = """        # MTF Ortalama (15m + 1h)
        columns_mtf = [
            "name", "close", "change", 
            "high|15", "low|15", "volume|15", "RSI|15", "MACD.macd|15", "MACD.signal|15", "EMA20|15", "EMA50|15", "EMA200|15", "ATR|15", "VWAP|15", "Stoch.K|15", "ADX|15", "Volatility.D|15", "average_volume_10d_calc|15", "ChaikinMoneyFlow|15", "open|15",
            "high|60", "low|60", "volume|60", "RSI|60", "MACD.macd|60", "MACD.signal|60", "EMA20|60", "EMA50|60", "EMA200|60", "ATR|60", "VWAP|60", "Stoch.K|60", "ADX|60", "Volatility.D|60", "average_volume_10d_calc|60", "ChaikinMoneyFlow|60", "open|60"
        ]"""
content = content.replace(old_columns, new_columns)
content = content.replace('columns_15m', 'columns_mtf')
content = content.replace('columns_60m', 'columns_mtf')


old_missing_part = """    @staticmethod
    def _missing_indicator_fields(values: List[Any]) -> List[str]:"""
    
new_missing_part = """    def _parse_mtf_row(self, clean_sym: str, raw_sym: str, market: str, vals: List[Any], now: float, is_rth: bool, benchmark_change: float) -> Optional[Dict[str, Any]]:
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
        
        high_60, low_60 = round(float(vals[20] or price), prec), round(float(vals[21] or price), prec)
        vol_60 = float(vals[22] or 0)
        rsi_60_v = vals[23]; rsi_60 = float(rsi_60_v) if rsi_60_v is not None else 50.0
        macd_60 = float(vals[24] or 0.0)
        ema20_60, ema50_60, ema200_60 = float(vals[26] or price), float(vals[27] or price), float(vals[28] or price)
        atr_60 = float(vals[29] or 0.0)
        stoch_60 = vals[31]; stoch_k_60 = float(stoch_60) if stoch_60 is not None else 50.0
        adx_60 = vals[32]; adx_60_val = float(adx_60) if adx_60 is not None else 20.0
        vol_avg_60 = float(vals[34] if len(vals) > 34 and vals[34] else vol_60)
        cmf_60 = float(vals[35] if len(vals) > 35 and vals[35] else 0.0)
        open_60 = round(float(vals[36] if len(vals) > 36 and vals[36] else price), prec)

        rsi_blended = round((rsi_15 * 0.4) + (rsi_60 * 0.6), 2)
        macd_blended = round((macd_15 * 0.4) + (macd_60 * 0.6), 2)
        stoch_k_blended = round((stoch_k_15 * 0.4) + (stoch_k_60 * 0.6), 2)
        adx_blended = round((adx_15_val * 0.4) + (adx_60_val * 0.6), 2)
        cmf_blended = round((cmf_15 * 0.4) + (cmf_60 * 0.6), 3)
        atr_blended = (atr_15 * 0.4) + (atr_60 * 0.6)
        ema_golden_cross = (ema20_15 > ema50_15 and ema50_15 > ema200_15) or (ema20_60 > ema50_60 and ema50_60 > ema200_60)

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
            "source": "TRADINGVIEW_LIVE_SCANNER",
            "last_update": time.strftime("%H:%M:%S"),
            "last_updated_ts": now,
            "source_timestamp": now,
            "missing_fields": self._missing_indicator_fields(vals)
        }

    @staticmethod
    def _missing_indicator_fields(values: List[Any]) -> List[str]:"""
content = content.replace(old_missing_part, new_missing_part)

def custom_replace_loop(content, marker, replacement):
    # Instead of regex, let's use string operations since we know the exact blocks
    # marker is what we find, e.g. "for item in data:"
    idx = 0
    blocks_found = 0
    while True:
        idx = content.find(marker, idx)
        if idx == -1: break
        
        # Is this the second loop inside the US, TR, CRYPTO sections?
        # Yes, we can just replace everything from `if len(vals) >= 16:` to `results[clean_sym] = { ... }`
        
        # Find `if len(vals) >= 16:`
        start_if = content.find("if len(vals) >= 16:", idx)
        if start_if != -1 and (start_if - idx) < 200:
            # We found the inner block! Now find where the `results[clean_sym] = {` ends
            end_dict = content.find("missing_fields\": self._missing_indicator_fields(vals)\n                            }", start_if)
            if end_dict != -1:
                end_block = end_dict + len("missing_fields\": self._missing_indicator_fields(vals)\n                            }")
                
                # Determine which market we are in by checking what comes shortly after
                # if it is self.cached_us_data, etc.
                next_text = content[end_block:end_block+500]
                if "self.cached_us_data =" in next_text:
                    market = "NASDAQ"
                    is_rth_str = "is_rth = (status_tuple[0] and status_tuple[2].get('session', 'RTH') == 'RTH')"
                elif "self.cached_tr_data =" in next_text:
                    market = "BIST"
                    is_rth_str = "is_rth = status_tuple[0]"
                else:
                    market = "CRYPTO"
                    is_rth_str = "is_rth = True"
                
                new_block = f"""
                        import time as time_mod
                        from services.risk_engine.market_hours import market_hours_validator
                        try:
                            status_tuple = market_hours_validator.is_market_open(clean_sym)
                            {is_rth_str}
                        except Exception:
                            is_rth = True
                        
                        parsed = self._parse_mtf_row(clean_sym, raw_sym, "{market}", vals, now, is_rth, benchmark_change)
                        if parsed:
                            results[clean_sym] = parsed"""
                
                content = content[:start_if] + new_block + content[end_block:]
                blocks_found += 1
                
        idx += 10 # Move forward
        
    return content

content = custom_replace_loop(content, "for item in data:", "")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("SUCCESS! File modified via AST-like parsing.")

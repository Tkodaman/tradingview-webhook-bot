import time
import asyncio
from fastapi import APIRouter
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from services.risk_engine.market_hours import market_hours_validator
from services.market_feed.live_stream import live_trade_manager
from services.risk_engine.fakeout_guard import fakeout_guard
import subprocess
import threading

router = APIRouter()
rsi_history = {}
_macro_voice_state = {"CRYPTO": {"last_spoken": 0}, "NASDAQ": {"last_spoken": 0}, "BIST": {"last_spoken": 0}}

def speak_turkish(text):
    import requests, urllib.parse, subprocess, time, os
    try:
        url = f'https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(text)}&tl=tr&client=tw-ob'
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            filename = f"voice_alert_{int(time.time())}.mp3"
            with open(filename, 'wb') as f:
                f.write(res.content)
            
            ps_cmd = f'''
            Add-Type -AssemblyName presentationCore
            $mp = New-Object system.windows.media.mediaplayer
            $mp.open('{filename}')
            $mp.Play()
            Start-Sleep -Seconds 10
            $mp.Stop()
            $mp.Close()
            Remove-Item -Path '{filename}' -ErrorAction SilentlyContinue
            '''
            subprocess.Popen(['powershell', '-Command', ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
    except:
        pass
# Kisa cache — karar matrix'i dashboard'da stale görünmesin.
_matrix_cache = {"data": None, "ts": 0}
_CACHE_TTL = 1  # saniye
_matrix_lock = asyncio.Lock()
_score_history = {}  # { "AAPL": [(timestamp, score), ...], ... }


def _number(value, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default

def _rsi_contribution(rsi: float) -> float:
    """RSI için tek, birleşik puan katkısı — çift sayımı önler.
    Adil yarış: RSI 25-40 (aşırı satım dip) en yüksek potansiyel alır,
    RSI 40-55 (dipten dönüş) ikinci, RSI 55-65 (trend güçlü) üçüncü,
    RSI 65-75 (olgun trend) nötr, RSI>=75 (aşırı alım) ceza alır.
    """
    if rsi >= 75.0:  return -10.0  # Aşırı alım / zirve riski (Şişkin)
    elif rsi >= 68.0: return -3.0  # Trendin sonları / yorgunluk (Tepeden alma riski)
    elif rsi >= 60.0: return +1.0  # Güçlü ama olgunlaşmış trend
    elif rsi >= 50.0: return +4.0  # Erken kırılım (Fresh Breakout)
    elif rsi >= 40.0: return +6.0  # Dipten dönüş / sessiz birikim (Önceden keşif)
    elif rsi >= 25.0: return +8.0  # Aşırı satım — dip fırsat
    else:             return -5.0  # Serbest düşüş paniği

@router.get("/live-matrix")
async def get_live_buy_sell_wait_matrix():
    """
    Anlik Gercek Zamanli BUY / SELL / WAIT Canli Sinyal Kokpiti
    5 saniye önbellekle TradingView yükünü azaltır; snapshot yaş kapısı ayrıca uygulanır.
    """
    global _matrix_cache
    
    # Hızlı kontrol (Kilitsiz - Fast Path)
    now = time.time()
    if _matrix_cache["data"] is not None and (now - _matrix_cache["ts"]) < _CACHE_TTL:
        return _matrix_cache["data"]

    # Eğer cache yoksa veya süresi dolmuşsa kilit bekle
    async with _matrix_lock:
        # Kilit açıldığında başka bir request cache'i doldurmuş olabilir (Double-checked locking)
        now = time.time()
        if _matrix_cache["data"] is not None and (now - _matrix_cache["ts"]) < _CACHE_TTL:
            return _matrix_cache["data"]
        
        live_data = await asyncio.to_thread(tradingview_live_client.fetch_live_market_data)

    overview = market_hours_validator.get_market_overview()
    matrix_results = []
    t_sec = int(time.time() * 1.5)
    
    for sym, data in live_data.items():
        # === TOXIC ASSET GUARD ===
        toxic_keywords = ["PAXG", "USDTUSD", "USDC", "TUSD", "BUSD", "DAI", "FDUSD", "XAUT", "EURUSD", "GBPUSD"]
        if any(toxic in sym.upper() for toxic in toxic_keywords):
            continue
            
        base_price = float(data.get("price", 0.0))
        quality_fields = ("rsi", "macd", "volume_ratio", "atr_pct", "adx", "cmf")
        missing_fields = list(data.get("missing_fields") or [])
        available_quality_fields = [field for field in quality_fields if field not in missing_fields and data.get(field) is not None]
        indicator_coverage = round(len(available_quality_fields) / len(quality_fields), 2)
        source_ts = float(data.get("source_timestamp") or data.get("last_updated_ts") or 0.0)
        data_age_seconds = round(max(0.0, time.time() - source_ts), 1) if source_ts > 0 else None
        stale_snapshot = data_age_seconds is None or data_age_seconds > 180.0
        critical_missing = [field for field in ("rsi", "macd", "volume_ratio", "adx", "cmf") if field in missing_fields or data.get(field) is None]
        if "atr" in missing_fields or data.get("atr_pct") is None:
            critical_missing.append("atr")
        data_gate_blocked = stale_snapshot or bool(critical_missing)
        data_quality = "STALE" if stale_snapshot else ("INSUFFICIENT" if critical_missing else "FULL")
        decision_gate = "DATA_BLOCKED" if data_gate_blocked else "ALLOW_ENTRY"
        rsi = _number(data.get("rsi"), 50.0)
        macd = _number(data.get("macd"), 0.0)
        vol_ratio = _number(data.get("volume_ratio"), 0.0)
        chg = _number(data.get("change_pct"), 0.0)
        
        # Piyasa türünü ve durumunu belirle
        market = data.get("market") or market_hours_validator.get_market_type(sym)
        if market not in ["CRYPTO", "BIST", "NASDAQ"]:
            market = market_hours_validator.get_market_type(sym)
            
        market_status = overview.get(market, {"is_open": False, "status_badge": "🔴 KAPALI", "session_text": ""})
        is_open = market_status.get("is_open", False)
        
        # Gerçek fiyatı kullan (yapay dalgalanma kaldırıldı)
        price = base_price
        
        # OTONOM GÖLGE ARENA DİNAMİK FİYAT & PNL GÜNCELLEMESİ (Canlı İz Sürme)
        if sym in live_trade_manager.shadow_positions:
            pos = live_trade_manager.shadow_positions[sym]
            if pos.status == "OPEN" and price > 0:
                pos.current_price = price
                pos.unrealized_pnl = (price - pos.entry_price) * pos.quantity
                pos.unrealized_pnl_pct = ((price - pos.entry_price) / pos.entry_price) * 100
                
                # Canlı TP/SL & Vur-Kaç (8 Saat) Kontrolü
                from datetime import datetime, timezone
                try:
                    if getattr(pos, 'opened_at', None):
                        if 'UTC' in pos.opened_at:
                            opened_dt = datetime.strptime(pos.opened_at.replace(' UTC', ''), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                        else:
                            opened_dt = datetime.fromisoformat(pos.opened_at)
                        duration_mins = int((datetime.now(timezone.utc) - opened_dt).total_seconds() / 60)
                    else:
                        duration_mins = 5
                except ValueError:
                    duration_mins = 5
                # Dinamik Vur-Kaç / Zaman Aşımı (Timeout) Süreleri
                if pos.market == "CRYPTO":
                    max_duration = 60  # Kripto için 1 saat (Agresif Skalper/Hız Avcısı)
                else:
                    max_duration = 120  # NASDAQ/BIST için 2 saat (Yüksek Veri Döngüsü)
                is_timeout = duration_mins >= max_duration
                
                if price >= pos.target_profit_price or price <= pos.stop_loss_price or is_timeout:
                    from services.engine.experience_memory_engine import experience_memory_engine, TradePostMortem
                    is_win = price >= pos.entry_price
                    sim_trade = TradePostMortem(
                        trade_id=pos.id,
                        symbol=pos.symbol,
                        action="BUY",
                        entry_price=pos.entry_price,
                        exit_price=price,
                        pnl_amount=pos.unrealized_pnl,
                        pnl_pct=pos.unrealized_pnl_pct,
                        is_win=is_win,
                        market_regime=pos.entry_indicators.get("market_regime", "DİNAMİK YARIŞ SÜZGECİ"),
                        indicators_at_entry={"score": pos.confidence_score},
                        lesson_learned=f"Canlı Gölge Arena: {'Hedef Vurdu' if is_win else 'Stop Patladı'}",
                        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                        duration_minutes=duration_mins,
                        exit_reason="Otonom TP (Test)" if is_win else "Zarar Kes (Test)",
                        algorithmic_action_plan="Saniyede bir güncellenen Liyakat Süzgeci'nde dinamik çıkış gerçekleşti."
                    )
                    experience_memory_engine.trade_history.append(sim_trade)
                    experience_memory_engine.save_memory()
                    pos.status = "CLOSED_TEST"
                    try:
                        from services.engine.bot_thought_stream import bot_thought_stream
                        bot_thought_stream.add_throttled(
                            category="⚔️ GÖLGE KAPANDI", 
                            symbol=sym, 
                            message=f"Skor {pos.confidence_score} ile alınan işlem {'KÂR' if is_win else 'ZARAR'} ile kapandı! PnL: %{pos.unrealized_pnl_pct:.2f}", 
                            level="WARN", 
                            cooldown_sec=10
                        )
                    except Exception:
                        pass

        # RSI Geçmişi Takibi
        if sym not in rsi_history:
            rsi_history[sym] = []
        rsi_history[sym].append(rsi)
        if len(rsi_history[sym]) > 10:
            rsi_history[sym].pop(0)
            
        hist = rsi_history[sym]
        rsi_climbed_from_40 = False
        if len(hist) >= 3 and rsi > 55.0:
            # Varlık 40'dan 55'e düzenli/kademeli çıktı mı?
            min_recent_rsi = min(hist)
            if 40.0 <= min_recent_rsi <= 50.0 and hist[-1] > hist[-2]:
                rsi_climbed_from_40 = True

        # OTONOM ML & YÜKSELİŞ POTANSİYELİ PUANLAMASI (Standart Yarış Modu)
        score = 0
        
        stoch_k_value = _number(data.get("stoch_k"), 50.0)
        adx_value = _number(data.get("adx"), 25.0)
        cmf_value = _number(data.get("cmf"), 0.0)
        atr_pct_value = _number(data.get("atr_pct"), 1.5)
        supertrend_bullish_value = bool(data.get("supertrend_bullish", False))
        
        candle_high = _number(data.get("candle_high"), price)
        candle_low = _number(data.get("candle_low"), price)
        candle_open = _number(data.get("candle_open"), price)
        
        # 1. RSI Katkısı — BİRLEŞİK FONKSİYON (eski çift sayım kaldırıldı)
        score += _rsi_contribution(rsi)
        
        # 2. Diğer Temel İndikatörler
        if macd >= 0.0: score += 1
        if data.get("ema_golden_cross", False): score += 2  # Güçlü sinyal
        if data.get("vwap_bullish", False): score += 1
        
        if vol_ratio >= 1.5: score += 3  # Hacim patlaması (Balina)
        elif vol_ratio >= 0.80: score += 1
        
        if 20.0 <= stoch_k_value <= 80.0: score += 1
        if adx_value >= 20.0: score += 1  # Trend yeni başlıyor/güçleniyor
        if cmf_value > 0.10: score += 2   # Yüksek Kurumsal Para Girişi
        elif cmf_value < -0.10: score -= 2  # Kurumsal çıkış — ceza
        if chg >= 0.5 and vol_ratio >= 1.2: score += 2  # Momentum Impulse
        
        # 2.5 Nyao Scalper - Wick Rejection Penalty (Üst Fitil Reddi)
        candle_range = candle_high - candle_low
        if candle_range > (price * 0.001): # Çok küçük dalgalanmaları yoksay (en az binde 1)
            upper_wick = candle_high - price
            upper_wick_ratio = upper_wick / candle_range
            # Eğer üst fitil mumun yarısından (%50) büyükse, sert satış baskısı var demektir
            if upper_wick_ratio > 0.5:
                penalty = 4.0 * upper_wick_ratio  # 0.5 ile 1.0 arası oran -> 2.0 ile 4.0 arası puan cezası
                score -= penalty
        
        # 3. Momentum Fazı — Hacim + RSI + CHG kombinasyonu (Geç Kalmama Kalkanı)
        momentum_phase = "NEUTRAL"
        
        # Eğer varlık halihazırda %2.5'ten fazla uçmuşsa, tepeden alma riskimiz (iğne yeme) çok yüksektir! (Kullanıcı Kalkanı)
        if chg >= 2.5:
            score -= 5
            momentum_phase = "LATE_ENTRY_RISK"
        elif vol_ratio >= 2.0:
            if chg < -1.5:
                score -= 5  # Çöküş Panik Satışı
                momentum_phase = "PANIC_DUMP"
            else:
                score += 4
                momentum_phase = "WHALE_WAVE_EARLY"
        elif 40.0 <= rsi <= 60.0 and data.get("ema_golden_cross", False):
            score += 4
            momentum_phase = "FRESH_BREAKOUT"
        elif rsi < 35.0 and vol_ratio >= 1.3:
            momentum_phase = "EARLY_EXPLOSION"  # Aşırı satım + yükselen hacim = dip toparlanması
        
        # 2. ML Otonom Hafıza Katkısı (Geçmiş başarıya göre ekstra puan)
        from services.engine.experience_memory_engine import experience_memory_engine
        ml_eval = experience_memory_engine.evaluate_signal_against_memory(sym, "BUY", {"rsi": rsi, "volume_ratio": vol_ratio}, "LIVE_MATRIX")
        if ml_eval["is_safe"]:
            score += int(ml_eval["confidence_modifier"] * 10.0) # +0.20 -> +2 puan
        else:
            score -= 10 # TOXIC ASSET ENGELİ
        
        open_pos = next((p for p in live_trade_manager.positions.values() if p.symbol.upper() == sym.upper() and p.status == "OPEN"), None)
        
        # === KAZAN-KAZAN: RİSK KALKANI ENTEGRASYONU (DASHBOARD SKORU İÇİN) ===
        stoch_k = _number(data.get("stoch_k"), 50.0)
        cmf = _number(data.get("cmf"), 0.0)
        atr_pct = _number(data.get("atr_pct"), 1.5)
        adx = _number(data.get("adx"), 25.0)
        ema_golden = data.get("ema_golden_cross", False)
        supertrend_bullish = bool(data.get("supertrend_bullish", False))
        
        fakeout_res = fakeout_guard.check(
            symbol=sym, price=price, change_pct=chg, vol_ratio=vol_ratio,
            rsi=rsi, cmf=cmf, stoch_k=stoch_k, atr_pct=atr_pct
        )
        
        risk_block_reason = None
        if vol_ratio < 0.5:
            score -= 10
            momentum_phase = "DEAD_VOLUME"
            risk_block_reason = f"💀 Ölü Tahta (Hacim Yok: {vol_ratio}x)"
        elif fakeout_res.is_fakeout:
            score -= 10
            momentum_phase = "FAKEOUT_RISK"
            short_reason = fakeout_res.reason.split(":")[-1].strip() if ":" in fakeout_res.reason else fakeout_res.reason
            risk_block_reason = f"🚨 Sahte Kırılım ({short_reason})"
        elif vol_ratio < 0.9:
            score -= 5
            momentum_phase = "VOLUME_RISK"
            risk_block_reason = f"💤 Hacimsiz (Vol: {vol_ratio}x)"
        elif adx < 20.0 and chg > 0.5 and not ema_golden and vol_ratio < 1.2:
            score -= 2
            momentum_phase = "WEAK_TREND"
            # risk_block_reason = ... (İptal edildi, analiz felcine yol açıyordu)
        elif ema_golden and not supertrend_bullish:
            score -= 3
            momentum_phase = "MIXED_TREND"
            # risk_block_reason = ... (İptal edildi, erken trendleri blokluyordu)
            
        # === YALITILMIŞ BÜÜE VE KAPASITE DİSİPLİNİ ===
        # Kripto (Binance) ve Hisse Senedi (Alpaca) birbirinden ÜzelÜ tutulur.
        # Kripto: maks 10 pozisyon, Hisse: maks 12 pozisyon.
        is_crypto_sym = ("USDT" in sym.upper() or sym.upper().endswith("BTC") or "/" in sym)
        if is_crypto_sym:
            crypto_open = [p for p in live_trade_manager.positions.values() if p.status == "OPEN" and p.market == "CRYPTO"]
            crypto_invested = sum(p.nominal_value for p in crypto_open)
            market_limit = 6
            market_open_count = len(crypto_open)
            budget_used = crypto_invested
            budget_limit = 1200.0  # Binance tarafı
        else:
            stock_open = [p for p in live_trade_manager.positions.values() if p.status == "OPEN" and p.market != "CRYPTO"]
            stock_invested = sum(p.nominal_value for p in stock_open)
            market_limit = 12
            market_open_count = len(stock_open)
            budget_used = stock_invested
            budget_limit = 8000.0  # Alpaca tarafı
        
        if not open_pos and not risk_block_reason:
            if market_open_count >= market_limit:
                risk_block_reason = f"Bütçe Dolu ({market_open_count}/{market_limit} pozisyon). Nadir fırsatlar için rotasyon modu bekleniyor."
            elif budget_limit > 0 and budget_used >= (budget_limit * 0.92):
                # Bütüenin %92'si dolysa sadece çok güçlü fırsatlar girebilir
                if score < 6:
                    risk_block_reason = f"Bütçe Esneme Bölgesinde (${budget_used:.0f}/${budget_limit:.0f}). Güçlü fırsatlar için saklanıyor (Skor: {score})."
            
        active_positions_list = [
            p for p in live_trade_manager.positions.values() 
            if p.status == "OPEN" and p.market == market
        ]
        try:
            from services.risk_engine.rotation_engine import rotation_engine
        except ImportError:
            rotation_engine = None

        rotation_check = {"rotate": False}
        if not open_pos and not risk_block_reason and not data_gate_blocked:
            try:
                if rotation_engine:
                    rotation_check = rotation_engine.evaluate_rotation(sym, score, data, active_positions_list)
            except Exception:
                pass

        if not is_open:
            decision = "WAIT"
            badge = "🔴 PİYASA KAPALI"
            reason = "Seans saatleri dışında olduğu için işlem yapılamaz."
        elif open_pos:
            decision = "HOLD"
            badge = "🟢 POSITION_OPEN"
            reason = f"Açık Pozisyon Aktif (Giriş: ${open_pos.entry_price}, PnL: ${open_pos.unrealized_pnl})"
        elif rotation_check.get("rotate", False):
            decision = "ROTATE"
            badge = "🔄 ROTASYON ONAYI"
            reason = rotation_check.get("reason", "Nadir ve güçlü kâr fırsatı yakalandı, rotasyon öneriliyor.")
            score += 15 # Rotasyon sinyalini en üste taşımak için devasa puan
        elif risk_block_reason:
            decision = "WAIT"
            badge = "🚧 RISK_BLOCK"
            reason = risk_block_reason
            
            # GÖLGE İŞLEM ENJEKSİYONU (Manuel Trade İçin) - SADECE PİYASA AÇIKSA!
            if is_open and score >= 5 and vol_ratio >= 1.5:
                try:
                    from services.engine.bot_thought_stream import bot_thought_stream
                    sl_level = price * (1 - (atr_pct / 100))
                    tp_level = price * (1 + (atr_pct * 2 / 100))
                    msg = f"GÖLGE İŞLEM (Manuel Fırsat): {sym} tetiklendi. Skor: {score}, Hacim: {vol_ratio:.2f}x. Engel Nedeni: {risk_block_reason}. Manuel giriş Pivot: ${price:.6f} | Hedef: ${tp_level:.6f} | Stop: ${sl_level:.6f}"
                    bot_thought_stream.add_throttled(
                        category="⚡ GÖLGE İŞLEM", 
                        symbol=sym, 
                        message=msg, 
                        level="WARN", 
                        cooldown_sec=120
                    )
                    # Sınır Tanımayan Gölge İşlem Ataması (Gölge Arena için)
                    live_trade_manager.open_shadow_position(
                        symbol=sym,
                        side="BUY",
                        tp_pct=atr_pct * 2,
                        sl_pct=atr_pct,
                        entry_price_override=price,
                        reason=risk_block_reason
                    )
                except Exception:
                    pass
        elif data_gate_blocked:
            decision = "WAIT"
            badge = "⏳ DATA_BLOCKED"
            missing_text = ", ".join(critical_missing) if critical_missing else "snapshot_timestamp"
            age_text = f"{data_age_seconds:.1f}s" if data_age_seconds is not None else "bilinmiyor"
            reason = f"⚠️ Eksik Veri Bekletildi (Yaş: {age_text})"
        elif not is_open:
            decision = "WAIT"
            badge = "💤 SEANS_DISI"
            reason = f"Piyasa Kapalı: {market_status.get('session_text', 'Seans saatleri dışında')}"
        elif rsi > 85.0 or macd < -1.5:
            decision = "SELL"
            badge = "🔴 SELL_SIGNAL"
            if rsi > 85.0:
                reason = f"🔥 Aşırı Şişkinlik (RSI={rsi:.1f})"
            else:
                reason = "📉 Negatif MACD (Satıcı Baskısı)"
        elif score >= 6 and vol_ratio >= 2.5:
            decision = "BUY"
            badge = "🟢 EXPLOSIVE_BREAKOUT"
            reason = f"Hacim Patlaması (Vol: {vol_ratio:.1f}x) ve Yüksek Skor ({score})"
            
            # Detaylı Neden Ekleme (Opsiyonel)
            adx_val = _number(data.get("adx"), 0.0)
            if data.get("vwap_bullish", False):
                reason += " | VWAP Üstü Kurumsal Destek"
            elif data.get("ema_golden_cross", False):
                reason += " | EMA Golden Cross (20>50>200)"
                
        elif rsi_climbed_from_40 and vol_ratio >= 2.0 and score >= 4:
            decision = "BUY"
            badge = "🟢 MOMENTUM_BUY"
            reason = f"Hacimli RSI İvmesi (Vol: {vol_ratio:.1f}x, Skor: {score})"
        else:
            decision = "WAIT"
            badge = "🟡 WAIT_PATIENT"
            if 40 <= rsi <= 60:
                reason = "⏳ Yatay Konsolidasyon (Kırılım Bekleniyor)"
            else:
                reason = "⚠️ Uyumsuz İndikatör (Teyit Bekleniyor)"
            
        high = round(float(data.get("high", price * 1.015)), 4 if price < 1.0 else 2)
        low = round(float(data.get("low", price * 0.985)), 4 if price < 1.0 else 2)
            
        matrix_results.append({
            "symbol": sym,
            "market": market,
            "is_market_open": is_open,
            "market_status_badge": market_status.get("status_badge", "🔴 KAPALI"),
            "market_session_text": market_status.get("session_text", ""),
            "price": price,
            "change_pct": chg,
            "high": high,
            "low": low,
            "rsi": rsi,
            "volume_ratio": vol_ratio,
            "adx": adx_value,
            "cmf": cmf_value,                    # ← YENİ: Kurumsal para akışı
            "atr_pct": atr_pct_value,             # ← YENİ: Dinamik TP için ATR
            "stoch_k": stoch_k_value,             # ← YENİ: Stochastic K
            "supertrend_bullish": supertrend_bullish_value,  # ← YENİ: Trend onayı
            "indicator_coverage": indicator_coverage,
            "data_quality": data_quality,
            "data_age_seconds": data_age_seconds,
            "missing_fields": critical_missing,
            "decision_gate": decision_gate,
            "score": score,
            "momentum_phase": momentum_phase,
            "decision": decision,
            "badge": badge,
            "reason": reason,
            "last_update": data.get("last_update", time.strftime("%H:%M:%S"))
        })
        
    # AI Güven Skoru Entegrasyonu
    from services.engine.experience_memory_engine import experience_memory_engine
    confidence_data = experience_memory_engine.get_asset_confidence_index()
    confidence_map = {item["symbol"].upper(): item for item in confidence_data}
    
    for m in matrix_results:
        sym = m["symbol"].upper()
        ai_data = confidence_map.get(sym, {})
        historical_sample = int(ai_data.get("total_trades", 0) or 0) if ai_data else 0

        # ══════════════════════════════════════════════════════════════════════
        # ADİL YARIŞ: AĞIRLIKLI DİLİM (WEIGHTED SLICE) GÜVEN SKORU MİMARİSİ
        # Her sinyal grubu sabit bir pasta dilimine sahip (toplam = 100 puan).
        # Her grup kendi dilimi içinde 0.0 → 1.0 arası normalize edilmiş performans
        # gösterir. Çift sayım, bonus yığılması ve yapay şişirme tamamen ortadan
        # kalktı. Yalnızca gerçek sinyal gücü sıralamayı belirler.
        #
        # DİLİM AĞIRLIKLARI (toplam = 100):
        #   RSI Momentum      : %20  → Fiyat gücü ve dönüş ivmesi
        #   Hacim/CMF         : %25  → Kurumsal para akışı ve katılım
        #   Teknik İndikatörler: %20 → ADX, Stoch, SuperTrend, pozisyon
        #   Fiyat Değişimi    : %10  → Gün içi erken/geç trend tespiti
        #   ML Geçmişi        : %15  → Deneyim hafızası, geçmiş başarı oranı
        #   Veri Kalitesi     : %10  → İndikatör kapsama ve veri tazeliği
        # ══════════════════════════════════════════════════════════════════════

        price     = m.get("price", 0.0)
        rsi       = float(m.get("rsi") or 50.0)
        vol_ratio = float(m.get("volume_ratio") or 1.0)
        cmf       = float(m.get("cmf") or 0.0)
        adx       = float(m.get("adx") or 0.0)
        stoch_k   = float(m.get("stoch_k") or 50.0)
        supertrend_b = bool(m.get("supertrend_bullish", False))
        chg_pct   = float(m.get("change_pct") or 0.0)
        ind_cov   = float(m.get("indicator_coverage") or 0.0)
        data_age  = float(m.get("data_age_seconds") or 999.0)
        high      = float(m.get("high") or price * 1.02)
        low       = float(m.get("low") or price * 0.98)

        # ── DİLİM 1: RSI MOMENTUM (%20) ──────────────────────────────────────
        # 30-45: dipten dönüş (güçlü)
        # 45-65: trend bölgesi (güçlü)
        # 65-75: ivme devam (orta)
        # <30 veya >75: uç bölge (düşük)
        if   rsi < 35:   rsi_raw = 0.0  # Serbest düşüş
        elif rsi < 45:   rsi_raw = 0.3  # Aşırı satım
        elif rsi < 55:   rsi_raw = 0.5  # Nötr
        elif rsi < 65:   rsi_raw = 0.8  # Trend başladı
        elif rsi < 72:   rsi_raw = 1.0  # İdeal ivme
        elif rsi < 78:   rsi_raw = 0.4  # Aşırı alım yaklaşıyor
        else:            rsi_raw = 0.0  # Düzeltme riski
        slice_rsi = rsi_raw * 20.0

        # ── DİLİM 2: HACİM & KURUMSAL PARA AKIŞI (%25) ───────────────────────
        # Hacim: 1x normal, 2x güçlü, 3x+ balina. CMF: -1→+1 kurumsal net akış.
        if   vol_ratio >= 4.0:  vol_raw = 1.0
        elif vol_ratio >= 3.0:  vol_raw = 0.8
        elif vol_ratio >= 2.0:  vol_raw = 0.6
        elif vol_ratio >= 1.5:  vol_raw = 0.4
        elif vol_ratio >= 1.0:  vol_raw = 0.2
        else:                   vol_raw = 0.0   # Ölü hacim — elensin

        # CMF bonusu: kurumsal net pozitif akış ek sinyal güç katkısı
        if   cmf > 0.20:  cmf_raw = 1.0
        elif cmf > 0.10:  cmf_raw = 0.75
        elif cmf > 0.0:   cmf_raw = 0.50
        elif cmf > -0.10: cmf_raw = 0.25
        else:             cmf_raw = 0.0

        # ── PİYASA BAZLI HACİM AĞIRLANDIRMASI ────────────────────────────────
        # NASDAQ ve CRYPTO için hacim farklı anlam taşır.
        market_type = m.get("market", "CRYPTO")

        if market_type == "NASDAQ":
            # NASDAQ: RTH (16:30-23:00 TRT) dışında (pre/post market) hacim
            # güvenilmez. Pre-market düşük hacimde büyük fiyat hareketi = yanıltıcı.
            # Session bilgisi market_router'da m["session"] olarak taşınır.
            session = m.get("session", "RTH")
            if session in ("PRE_MARKET", "POST_MARKET"):
                # Pre/post market: hacim ağırlığını %60 düşür, CMF'e ağırlık ver
                # Kurumsal yönü (CMF) RTH açılışını tahmin eder, ham hacim değil.
                vol_weight = 0.40   # Hacim güvenilirlik düşük
                cmf_weight = 0.60   # CMF yön bilgisi daha değerli
                # Pre-market hacim spike'larını cezalandır (stop hunt riski)
                if vol_ratio > 2.0:
                    vol_raw = min(vol_raw, 0.55)  # 2x+ spike'ları sınırla
            else:
                # RTH: Standart ağırlık — kurumsal blok alımları burada okunur
                vol_weight = 0.65
                cmf_weight = 0.35
            m["volume_session_note"] = f"NASDAQ {session}: Hac%{int(vol_weight*100)} CMF%{int(cmf_weight*100)}"

        elif market_type == "CRYPTO":
            # CRYPTO 7/24 açık. Salt hacim balina yönünü vermez.
            # CMF burada daha kritik — negatif CMF ile yükselen hacim = dağıtım.
            # ABD seansı (16:30-23:00 TRT) aktifse hacim daha güvenilir.
            import datetime as _dt
            from zoneinfo import ZoneInfo as _ZI
            _now_tr = _dt.datetime.now(_ZI("Europe/Istanbul"))
            _hour_tr = _now_tr.hour
            is_us_session = (16 <= _hour_tr < 23)

            if is_us_session:
                # ABD seansı: Hacim + CMF eşit önemde
                vol_weight = 0.60
                cmf_weight = 0.40
                # Negatif CMF + yüksek hacim = dağıtım cezası
                if cmf_raw == 0.0 and vol_raw >= 0.70:
                    vol_raw *= 0.65   # Yüksek hacim + negatif CMF → güvenilmez
            else:
                # Asia/Avrupa seansı: CMF daha baskın (hacim düşük, manipülasyon riski)
                vol_weight = 0.45
                cmf_weight = 0.55
                # Düşük seans + aşırı hacim spike'ı = wash trading şüphesi
                if vol_ratio > 3.0:
                    vol_raw = min(vol_raw, 0.70)
            m["volume_session_note"] = f"CRYPTO {'ABD' if is_us_session else 'ASYA/EU'}: Hac%{int(vol_weight*100)} CMF%{int(cmf_weight*100)}"

        else:
            # BIST veya diğer: Standart ağırlık
            vol_weight = 0.70
            cmf_weight = 0.30

        # Nihai Hacim+CMF dilim skoru (piyasaya özel ağırlıklar ile)
        slice_volume = ((vol_raw * vol_weight) + (cmf_raw * cmf_weight)) * 25.0


        # ── DİLİM 3: TEKNİK İNDİKATÖRLER (%20) ──────────────────────────────
        # ADX, Stoch K, SuperTrend, Gün içi fiyat pozisyonu
        tech_score = 0.0

        # ADX: Trend gücü (0-40 normalize)
        if   adx >= 40: adx_raw = 1.0
        elif adx >= 25: adx_raw = (adx - 25) / 15.0
        else:           adx_raw = adx / 50.0  # Zayıf trend
        tech_score += adx_raw * 0.35  # ADX dilim içi %35

        # Stoch K: Aşırı satımdan çıkış ve ideal bölge
        if   stoch_k < 20:  stoch_raw = 0.7  # Aşırı satım (fırsat)
        elif stoch_k < 50:  stoch_raw = 1.0  # İdeal bölge
        elif stoch_k < 70:  stoch_raw = 0.7  # Normal
        else:               stoch_raw = 0.2  # Aşırı alım
        tech_score += stoch_raw * 0.30  # Stoch dilim içi %30

        # SuperTrend: Trend yönü onayı
        tech_score += (1.0 if supertrend_b else 0.2) * 0.20  # SuperTrend dilim içi %20

        # Gün içi fiyat pozisyonu: Alt %30 = fırsat, Üst %70+ = riskli
        if high > low:
            pos_range = (price - low) / (high - low)
            if   pos_range <= 0.25: pos_raw = 1.0   # Dibe yakın = fırsat
            elif pos_range <= 0.50: pos_raw = 0.75
            elif pos_range <= 0.75: pos_raw = 0.50
            else:                   pos_raw = 0.15  # Zirveye yakın = riskli
        else:
            pos_raw = 0.5
        tech_score += pos_raw * 0.15  # Pozisyon dilim içi %15

        slice_technical = tech_score * 20.0

        # ── DİLİM 4: GÜNLÜK FİYAT DEĞİŞİMİ (%10) ────────────────────────────
        # 0.5%-3.5%: Uyanış sinyali (ideal erken giriş)
        # >6%: Trene sondan binme (olumsuz)
        # <-3%: Satış baskısı (olumsuz)
        if   0.5 <= chg_pct <= 1.5:  chg_raw = 1.0   # Taze uyanış
        elif 1.5 < chg_pct <= 3.5:   chg_raw = 0.85  # Momentum var
        elif 3.5 < chg_pct <= 6.0:   chg_raw = 0.55  # Zaten ısındı
        elif chg_pct > 6.0:          chg_raw = 0.15  # Geç kalındı
        elif -1.0 <= chg_pct < 0.5:  chg_raw = 0.55  # Nötr/hafif düşüş
        elif -3.0 <= chg_pct < -1.0: chg_raw = 0.30  # Satış var
        else:                        chg_raw = 0.05  # Sert düşüş
        slice_change = chg_raw * 10.0

        # ── DİLİM 5: ML GEÇMİŞİ / DENEYİM HAFIZASI (%15) ────────────────────
        # Gerçek geçmiş işlem başarısını yansıtır. Veri yoksa nötr (0.5).
        ai_bonus = 0.0
        if ai_data and "confidence_score" in ai_data:
            raw_conf = float(ai_data["confidence_score"])
            # Deneyim olgunluğu: 10 işlemden sonra tam ağırlık
            sample_factor = min(1.0, historical_sample / 10.0)
            # ML başarısını 0→1 arası normalize et (50% nötr, 100% tam)
            ml_raw = ((raw_conf - 50.0) / 50.0) * sample_factor  # -1.0 → +1.0
            # 0.0→1.0 arası dönüştür
            ml_normalized = max(0.0, min(1.0, 0.5 + ml_raw * 0.5))
            ai_bonus = ml_normalized
            if ml_normalized > 0.7:
                m["reason"] += f" | 🧠 ML:✅ ({historical_sample} geçmiş)"
            elif ml_normalized < 0.3:
                m["reason"] += f" | 🧠 ML:⚠️ ({historical_sample} geçmiş)"
        else:
            ai_bonus = 0.5  # KESİN KARAR: Veri yoksa asla sahte/cüretkar değer atanmaz. Tamamen Nötr (0.50).
        slice_ml = ai_bonus * 15.0

        # ── DİLİM 6: VERİ KALİTESİ (%10) ────────────────────────────────────
        # İndikatör kapsama oranı + veri tazeliği
        # Kapsama: ne kadar indikatör dolu (0→1)
        # Tazelik: son 30s mükemmel, 90s kabul edilebilir, üstü zayıf
        if   data_age <= 30:  freshness_raw = 1.0
        elif data_age <= 60:  freshness_raw = 0.85
        elif data_age <= 90:  freshness_raw = 0.65
        else:                 freshness_raw = 0.20

        # Kapsama %60, Tazelik %40 (dilim içi ağırlık)
        slice_quality = ((ind_cov * 0.60) + (freshness_raw * 0.40)) * 10.0

        # ── NİHAİ SKOR: 6 DİLİMİN ORANSAL TOPLAMI ───────────────────────────
        base_raw_score = (
            slice_rsi        +  # %20
            slice_volume     +  # %25
            slice_technical  +  # %20
            slice_change     +  # %10
            slice_ml         +  # %15
            slice_quality       # %10
        )
        
        # ── KONSEY & AJANLAR: AKILLI CÜRETKÂR FIRSAT SÜZGECİ (AYIRT EDİCİ BÖLÜM) ──
        # Kullanıcı Geri Bildirimi: Sadece körü körüne skoru şişirme, gerçek fırsatları adil şekilde öne çıkar!
        agent_bonus = 0.0
        
        # Ajan 1: Hacim + Momentum Patlaması (Balina Uyanışı)
        if vol_ratio > 2.0 and 50 <= rsi <= 68 and cmf > 0.05:
            agent_bonus += 5.0
            m["badge"] = "🐋 BALİNA"
            
        # Ajan 2: Sıkışma Kırılımı (Squeeze Breakout - Tam patlamaya hazır)
        is_consolidating = (40.0 <= rsi <= 55.0) and (adx < 25.0)
        if is_consolidating and vol_ratio > 1.8 and cmf > 0.05:
            agent_bonus += 5.0
            m["badge"] = "🧨 BOMBA"
            m["reason"] = f"🧨 SIKIŞMA KIRILIMI: Hacim {vol_ratio:.1f}x | CMF {cmf:.2f}"
            
        # Ajan 3: Yükselen Trendde Düşük Riskli Giriş (Golden Pocket)
        # Katı EMA Golden Cross şartı esnetildi: Kısa vadeli EMA (12>26 yani MACD>0) pozitifse o da kabul.
        is_golden_trend = data.get("ema_golden_cross", False) or (macd > 0.0)
        if is_golden_trend and 45 <= rsi <= 60 and vol_ratio >= 1.2:
            agent_bonus += 4.0
            m["badge"] = "🌟 ALTIN"
            
        # Ajan 4: Güçlü Trend Destekli Yükseliş
        if adx >= 25.0 and vol_ratio >= 1.5:
            agent_bonus += 3.0
            
        # Sığ piyasa veya hacimsiz ralli ise bonusları tamamen iptal et (Tuzak Koruması)
        if vol_ratio < 0.8:
            agent_bonus = 0.0
            
        # Adil Oransal Dağılım: Temel skor + Liyakat Bonusu. Yapay şişirme (1.10x) kaldırıldı!
        raw_score = base_raw_score + agent_bonus
        
        # ── KONSEY (ÖNERİ + 2) AĞIRLIKLI ORTALAMASI (KAOS ENGELLEYİCİ) ──
        # Listenin her tickte zıplamasını (kaotik yapıyı) engellemek için sadece son 3 veriyi tut
        if sym not in _score_history:
            _score_history[sym] = []
            
        _score_history[sym].append(raw_score)
        if len(_score_history[sym]) > 3:
            _score_history[sym].pop(0) # Sadece son 3'ü (Öneri + 2 Önceki) tut
            
        smoothed_score = raw_score
        hist_len = len(_score_history[sym])
        
        # Weighted Moving Average (Ağırlıklı Ortalama): Güncele (son veriye) daha fazla ağırlık
        if hist_len == 3:
            smoothed_score = (_score_history[sym][0]*1 + _score_history[sym][1]*2 + _score_history[sym][2]*3) / 6.0
        elif hist_len == 2:
            smoothed_score = (_score_history[sym][0]*1 + _score_history[sym][1]*2) / 3.0

        # ── KONSEY CEZALARI (ADİL PAYDA ORANI İÇİN ACIMASIZ SÜZGEÇ) ──
        # Yumuşatılmış skor üzerinden cezaları KESİN ve ANINDA uygula! Geçmişin hatırı cezalarda işlemez.
        if vol_ratio < 0.5:
            smoothed_score *= 0.40  # Ölü tahta: Skoru %60 tırpanla anında!
        elif vol_ratio < 0.8:
            smoothed_score *= 0.70  # Hacimsiz piyasa: Skoru %30 tırpanla anında!
            
        if risk_block_reason and ("Sahte" in risk_block_reason or "Fake" in risk_block_reason):
            smoothed_score *= 0.50  # Sahte Kırılım tuzağı tespit edildiyse skoru direkt yarıya indir!
        
        ranking_score = round(max(0.0, min(99.9, smoothed_score)), 1)
        confidence_score = ranking_score

        # Veri kalitesi yetersizse skoru bloke et
        if m.get("decision_gate") != "ALLOW_ENTRY":
            ranking_score    = 0.0
            confidence_score = 0.0

        # Dilim dağılımını debug için sakla
        m["score_breakdown"] = {
            "rsi_momentum":  round(slice_rsi, 2),
            "volume_cmf":    round(slice_volume, 2),
            "technical":     round(slice_technical, 2),
            "price_change":  round(slice_change, 2),
            "ml_history":    round(slice_ml, 2),
            "data_quality":  round(slice_quality, 2),
        }

        m["ranking_score"] = ranking_score
        m["confidence_score"] = confidence_score
        
        # ── OTONOM GÖLGE ARENA ENJEKSİYONU (Canlı Paper Trading) ──
        # Eğer liyakat süzgecinden başarıyla geçmiş ve yüksek skor almışsa, Gölge Arena'ya otonom test için at!
        if ranking_score >= 80.0 and m.get("is_market_open") and m.get("decision_gate") == "ALLOW_ENTRY":
            if sym not in live_trade_manager.shadow_positions and sym not in live_trade_manager.positions:
                import uuid
                from datetime import datetime, timezone
                from services.market_feed.live_stream import ActivePosition
                is_open, _, _ = market_hours_validator.is_market_open(sym)
                if not is_open:
                    continue
                
                new_shadow_pos = ActivePosition(
                    id=f"SHADOW_{uuid.uuid4().hex[:6].upper()}",
                    symbol=sym,
                    market=market,
                    side="BUY",
                    entry_price=price,
                    current_price=price,
                    quantity=100.0 / price if price > 0 else 0,
                    nominal_value=100.0,
                    target_profit_price=price * 1.05,
                    stop_loss_price=price * 0.97,
                    break_even_trigger_price=price * 1.015,
                    opened_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    confidence_score=ranking_score,
                    entry_indicators={"score": ranking_score, "market_regime": "DİNAMİK YARIŞ SÜZGECİ"}
                )
                live_trade_manager.shadow_positions[sym] = new_shadow_pos
                try:
                    from services.engine.bot_thought_stream import bot_thought_stream
                    bot_thought_stream.add_throttled(
                        category="⚔️ GÖLGE ARENA", 
                        symbol=sym, 
                        message=f"Skor %{ranking_score:.1f} ile Otonom Test Havuzuna fırlatıldı! (Ajan Onaylı)", 
                        level="WARN", 
                        cooldown_sec=300
                    )
                except Exception:
                    pass

        m["confidence_label"] = (
            "DATA_BLOCKED" if m.get("decision_gate") != "ALLOW_ENTRY" else
            "HIGH_EVIDENCE" if m["indicator_coverage"] >= 0.83 and historical_sample >= 20
            else "LIVE_TECHNICAL" if m["indicator_coverage"] >= 0.83
            else "PARTIAL_DATA"
        )
        m["historical_sample"] = historical_sample

    # --- YENİ: REVERSAL ENGINE (DİP AVCISI) KUTULARI (Grup filterindan ÖNCE eklenmeli ki dashboard'a yansısın) ---
    try:
        from services.risk_engine.reversal_engine import reversal_engine
        for rev_sym in reversal_engine.target_symbols:
            raw_sym = rev_sym.split(":")[-1] if ":" in rev_sym else rev_sym
            rev_data = live_data.get(raw_sym, {})
            rev_price = rev_data.get("price", 0.0)
            rev_rsi = rev_data.get("rsi", 0.0)
            rev_vol = rev_data.get("volume_ratio", 0.0)
            # RSI temelli gerçekçi güven skoru hesaplama
            realistic_conf = 100.0 - (rev_rsi * 1.2)
            realistic_conf = max(45.0, min(99.5, realistic_conf))
            if rev_vol > 1.5: realistic_conf = min(99.9, realistic_conf + 4.0)
            
            # Dinamik Durum Mesajı
            if rev_rsi <= 25 and rev_vol >= 1.5:
                rev_status = "🚀 MUAZZAM FIRSAT (Dip Görüldü, Alıma Hazır!)"
            elif rev_rsi <= 30:
                rev_status = "⚠️ Yoğun Bakım (Balina Hacmi Bekleniyor)"
            elif rev_rsi <= 45:
                rev_status = "🩸 Kanama Başladı (Düşüş Derinleşiyor)"
            else:
                rev_status = "💤 Uykuda (Kan Banyosu Bekleniyor...)"

            if reversal_engine.is_active:
                rev_status = "🔮 Otonom İnfaz Devrede (Kill-Switch Tetiklendi!)"
            
            rev_market = "CRYPTO"
            rev_open = True
            if "BIST:" in rev_sym:
                rev_market = "BIST"
                rev_open = is_bist_open if 'is_bist_open' in locals() else True
            elif "NASDAQ:" in rev_sym:
                rev_market = "NASDAQ"
                rev_open = is_nasdaq_open if 'is_nasdaq_open' in locals() else True

            matrix_results.append({
                "symbol": raw_sym,
                "market": rev_market,
                "is_market_open": rev_open,
                "price": rev_price,
                "change_pct": rev_data.get("change_pct", 0.0),
                "rsi": rev_rsi,
                "volume_ratio": rev_vol,
                "decision": "WAIT",
                "reason": rev_status,
                "is_reversal": True,
                "score": 0,
                "momentum_phase": "REVERSAL_MONITOR",
                "confidence_score": round(realistic_conf, 1),
                "indicator_coverage": 1.0
            })
    except Exception as e:
        print("Reversal Engine Entegrasyon Hatası:", e)

    # Varlıkları market bazında ayır
    crypto_all = [m for m in matrix_results if m["market"] == "CRYPTO"]
    bist_all = [m for m in matrix_results if m["market"] == "BIST"]
    nasdaq_all = [m for m in matrix_results if m["market"] == "NASDAQ"]

    # CRYPTO için Özel Sıralama: İlk 6 Momentum, Sonra Reversal, Sonra Diğer Momentumlar
    crypto_normal = sorted([m for m in crypto_all if not m.get("is_reversal")], key=lambda x: x.get("confidence_score", 0), reverse=True)
    crypto_reversal = sorted([m for m in crypto_all if m.get("is_reversal")], key=lambda x: x.get("confidence_score", 0), reverse=True)
    final_crypto = crypto_normal[:6] + crypto_reversal + crypto_normal[6:]

    # BIST için Özel Sıralama: İlk 6 Momentum, Sonra Reversal, Sonra Diğer Momentumlar
    bist_normal = sorted([m for m in bist_all if not m.get("is_reversal")], key=lambda x: x.get("confidence_score", 0), reverse=True)
    bist_reversal = sorted([m for m in bist_all if m.get("is_reversal")], key=lambda x: x.get("confidence_score", 0), reverse=True)
    final_bist = bist_normal[:6] + bist_reversal + bist_normal[6:]

    # NASDAQ için Özel Sıralama: İlk 6 Momentum, Sonra Reversal, Sonra Diğer Momentumlar
    nasdaq_normal = sorted([m for m in nasdaq_all if not m.get("is_reversal")], key=lambda x: x.get("confidence_score", 0), reverse=True)
    nasdaq_reversal = sorted([m for m in nasdaq_all if m.get("is_reversal")], key=lambda x: x.get("confidence_score", 0), reverse=True)
    final_nasdaq = nasdaq_normal[:6] + nasdaq_reversal + nasdaq_normal[6:]

    grouped_matrix = {
        "CRYPTO": final_crypto[:50],
        "BIST": final_bist[:15],
        "NASDAQ": final_nasdaq[:50]
    }
    
    # === GLOBAL MACRO FORESIGHT (SESLİ ÖNSEZİ) ===
    now_ts = time.time()
    for m_name, assets in grouped_matrix.items():
        if not assets: continue
        
        # Sadece 30 dakikada bir aynı anonsu tekrarla
        if now_ts - _macro_voice_state.get(m_name, {}).get("last_spoken", 0) < 1800:
            continue
            
        high_vol_dumps = [a for a in assets[:20] if a.get("rsi", 50) < 35 and a.get("volume_ratio", 1) > 1.2]
        high_vol_pumps = [a for a in assets[:20] if a.get("rsi", 50) > 65 and a.get("volume_ratio", 1) > 1.2]
        low_vol_stagnant = [a for a in assets[:20] if a.get("volume_ratio", 1) < 0.75]
        
        active_pos_count = len([p for p in live_trade_manager.positions.values() if p.status == "OPEN"])
        
        import random
        
        if len(high_vol_dumps) >= 5:
            _macro_voice_state[m_name] = {"last_spoken": now_ts}
            msg = random.choice([
                f"Dikkat komutan. {m_name} cephesinde sert bir çöküş paniği var. Nakitte beklemek en iyisi.",
                f"{m_name} piyasasında kan gövdeyi götürüyor. Balinalar satışa geçti, kalkanları kaldır.",
                f"Acil durum. {m_name} tarafında hacimli satışlar başladı, radarı izlemeye al."
            ])
            threading.Thread(target=speak_turkish, args=(msg,)).start()
        elif len(high_vol_pumps) >= 5:
            _macro_voice_state[m_name] = {"last_spoken": now_ts}
            msg = random.choice([
                f"Mükemmel haber. {m_name} tarafında mega boğa piyasası tetiklendi. Hacimler patlıyor.",
                f"{m_name} cephesinde roketler ateşlendi. Piyasaya devasa para girişi var.",
                f"Komutan, {m_name} piyasasında rüzgar arkamızda. Fırsatları değerlendirme zamanı."
            ])
            threading.Thread(target=speak_turkish, args=(msg,)).start()
        elif len(low_vol_stagnant) >= 10:
            _macro_voice_state[m_name] = {"last_spoken": now_ts}
            msg = random.choice([
                f"{m_name} piyasasında hacim tamamen kurumuş durumda. Fırsat yok, beklemede kalıyoruz.",
                f"{m_name} tarafında yaprak kıpırdamıyor. Enerjimizi boşa harcamayalım.",
                f"Sessizlik hakim. {m_name} cephesinde sığ sular, işlem yapmak için tehlikeli."
            ])
            threading.Thread(target=speak_turkish, args=(msg,)).start()
        elif active_pos_count >= 14 and m_name == "CRYPTO": # Sadece bir kere söylemesi için CRYPTO sekmesinde tetiklensin
            _macro_voice_state[m_name] = {"last_spoken": now_ts}
            msg = random.choice([
                f"Kasa kapasitesi doldu. İçeride çok fazla açık pozisyon var. Yeni alımlar durduruldu.",
                f"Komutan, maksimum portföy limitine ulaştık. Nakit koruma protokolü devrede.",
                f"Tüm slotlar dolu. Şuan sadece mevcut pozisyonları koruma ve devasa fırsatları izleme modundayız."
            ])
            threading.Thread(target=speak_turkish, args=(msg,)).start()

    result = {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "markets_overview": overview,
        "total_monitored_assets": len(matrix_results),
        "signals_summary": {
            "BUY":  len([m for m in matrix_results if m["decision"] == "BUY"]),
            "SELL": len([m for m in matrix_results if m["decision"] == "SELL"]),
            "WAIT": len([m for m in matrix_results if m["decision"] == "WAIT"]),
            "HOLD": len([m for m in matrix_results if m["decision"] == "HOLD"])
        },
        "grouped": grouped_matrix,
        "matrix": matrix_results
    }
    # Cache'e kaydet
    _matrix_cache["data"] = result
    _matrix_cache["ts"] = time.time()
    return result


@router.get("/market-index/three-way")
async def get_three_way_market_index():
    """
    3-Way Endeksli Piyasa Penceresi (NASDAQ, BIST, KRİPTO) canlı veri taraması
    """
    live_data = await asyncio.to_thread(tradingview_live_client.fetch_live_market_data)
    
    nasdaq_list = []
    bist_list = []
    crypto_list = []
    
    for sym, item in live_data.items():
        mkt = item.get("market", "UNKNOWN")
        is_open, msg, _ = market_hours_validator.is_market_open(sym)
        payload = {**item, "is_market_open": is_open, "market_status": msg}
        
        if mkt == "NASDAQ":
            nasdaq_list.append(payload)
        elif mkt == "BIST":
            bist_list.append(payload)
        elif mkt == "CRYPTO":
            crypto_list.append(payload)
            
    return {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "markets": {
            "NASDAQ": {
                "count": len(nasdaq_list),
                "is_open": market_hours_validator.is_market_open("NVDA")[0],
                "items": nasdaq_list
            },
            "BIST": {
                "count": len(bist_list),
                "is_open": market_hours_validator.is_market_open("THYAO")[0],
                "items": bist_list
            },
            "CRYPTO": {
                "count": len(crypto_list),
                "is_open": True,
                "items": crypto_list
            }
        }
    }

@router.get("/live-feed")
async def get_live_market_feed():
    """
    Canlı Borsa Hisse İniş Çıkışları ve Anlık Dalgalanma Akışı
    """
    return live_trade_manager.get_live_prices()

from services.data_ingestion.news_macro_feed import news_macro_feed
@router.get("/news")
async def get_live_news():
    return news_macro_feed.fetch_live_news()

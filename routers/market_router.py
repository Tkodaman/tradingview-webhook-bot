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
_CACHE_TTL = 5  # saniye
_matrix_lock = asyncio.Lock()
_score_history = {}  # { "AAPL": [(timestamp, score), ...], ... }


def _number(value, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default

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
        stale_snapshot = data_age_seconds is None or data_age_seconds > 45.0
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
        
        # 1. Temel İndikatörler (Tüm algoritmik değerler standart yarışır)
        if rsi >= 60.0: score += 2 # Güçlü trend
        elif rsi >= 50.0: score += 1 # Pozitif bölge
        
        if macd >= 0.0: score += 1
        if data.get("ema_golden_cross", False): score += 2 # Güçlü sinyal
        if data.get("vwap_bullish", False): score += 1
        
        if vol_ratio >= 1.5: score += 3 # Hacim patlaması (Balina)
        elif vol_ratio >= 0.80: score += 1
        
        stoch_k_value = _number(data.get("stoch_k"), 50.0)
        adx_value = _number(data.get("adx"), 25.0)
        cmf_value = _number(data.get("cmf"), 0.0)
        if 20.0 <= stoch_k_value <= 80.0: score += 1
        if adx_value >= 20.0: score += 1 # Trend yeni başlıyor/güçleniyor
        if cmf_value > 0.10: score += 2 # Yüksek Kurumsal Giriş
        if chg >= 0.5 and vol_ratio >= 1.2: score += 2 # Momentum Impulse
        
        momentum_phase = "NEUTRAL"
        if vol_ratio >= 2.0:
            if chg < -1.5:
                score -= 5 # Çöküş Panik Satışı
                momentum_phase = "PANIC_DUMP"
            else:
                score += 4
                momentum_phase = "WHALE_WAVE"
        elif 50.0 <= rsi <= 70.0 and data.get("ema_golden_cross", False):
            score += 3
            momentum_phase = "FRESH_BREAKOUT"
        elif rsi > 72.0 and chg > 3.0:
            score -= 3
            momentum_phase = "PEAK_RISK"
        
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
        if fakeout_res.is_fakeout:
            score -= 10
            momentum_phase = "FAKEOUT_RISK"
            risk_block_reason = f"Sahte Kırılım (Fakeout) Tespit Edildi: {fakeout_res.reason}"
        elif vol_ratio < 0.75:
            score -= 3
            momentum_phase = "VOLUME_RISK"
            risk_block_reason = "Aşırı Hacimsizlik (Vol < 0.75)"
        elif adx < 20.0 and chg > 0.5 and not ema_golden and vol_ratio < 1.2:
            score -= 2
            momentum_phase = "TREND_RISK"
            risk_block_reason = "Yatay Piyasada Sahte Yükseliş (ADX < 20)"
        elif ema_golden and not supertrend_bullish:
            score -= 5
            momentum_phase = "TREND_RISK"
            risk_block_reason = "Çelişen Trend Sinyali (EMA Boğa, Supertrend Ayı)"
            
        # ==========================================
        # KASA VE BÜTÇE DİSİPLİNİ (14 LİMİT & 9 YAVAŞLATMA EŞİĞİ)
        # ==========================================
        active_positions_list = [p for p in live_trade_manager.positions.values() if p.status == "OPEN"]
        total_active_count = len(active_positions_list)
        
        try:
            from services.risk_engine.rotation_engine import rotation_engine
        except ImportError:
            rotation_engine = None
        
        if not open_pos and not risk_block_reason: # Eğer halihazırda sahte sinyal engeli yoksa, bütçe engelini kontrol et
            if total_active_count >= 14:
                # Kasa tamamen dolu, SADECE ROTASYON yapılabilir. Düz alım yasak.
                rotate_ok = False
                if rotation_engine:
                    rotate_ok = rotation_engine.evaluate_rotation(sym, score, data, active_positions_list).get("rotate", False)
                if not rotate_ok:
                    risk_block_reason = f"Bütçe Dolu (Kapasite: {total_active_count}/14). Nakit bitti, sadece devasa fırsatlar için rotasyon izni var."
            elif total_active_count >= 9:
                # 9 Varlıktan sonra vites düşür (Nakit rezervini koru, sadece en yüksek fırsatlara kurşun at)
                if score < 7:
                    risk_block_reason = f"Kasa Yavaşlama Bölgesinde ({total_active_count}/14). Nakit rezervi sadece en kaliteli (Skor 7+) fırsatlar için bekletiliyor. Bu fırsat elendi (Skor: {score})."
            
        rotation_check = {"rotate": False}
        if not open_pos and not risk_block_reason and not data_gate_blocked:
            try:
                if rotation_engine:
                    rotation_check = rotation_engine.evaluate_rotation(sym, score, data, active_positions_list)
            except Exception:
                pass

        if open_pos:
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
            
            # GÖLGE İŞLEM ENJEKSİYONU (Manuel Trade İçin)
            if score >= 5 and vol_ratio >= 1.5:
                try:
                    from services.engine.bot_thought_stream import bot_thought_stream
                    sl_level = price * (1 - (atr_pct / 100))
                    tp_level = price * (1 + (atr_pct * 2 / 100))
                    msg = f"GÖLGE İŞLEM (Manuel Fırsat): {sym} tetiklendi. Skor: {score}, Hacim: {vol_ratio:.2f}x. Kasa kilitli olduğu için girilemedi. Manuel giriş Pivot: ${price:.4f} | Hedef: ${tp_level:.4f} | Stop: ${sl_level:.4f}"
                    bot_thought_stream.add_throttled(
                        category="⚡ GÖLGE İŞLEM", 
                        symbol=sym, 
                        message=msg, 
                        level="WARN", 
                        cooldown_sec=120
                    )
                except Exception:
                    pass
        elif data_gate_blocked:
            decision = "WAIT"
            badge = "⏳ DATA_BLOCKED"
            missing_text = ", ".join(critical_missing) if critical_missing else "snapshot_timestamp"
            age_text = f"{data_age_seconds:.1f}s" if data_age_seconds is not None else "bilinmiyor"
            reason = f"Yeni işlem bekletildi: veri yaşı {age_text}, eksik/geçersiz alanlar: {missing_text}"
        elif not is_open:
            decision = "WAIT"
            badge = "💤 SEANS_DISI"
            reason = f"Piyasa Kapalı: {market_status.get('session_text', 'Seans saatleri dışında')}"
        elif rsi > 85.0 or macd < -1.5:
            decision = "SELL"
            badge = "🔴 SELL_SIGNAL"
            if rsi > 85.0:
                reason = f"Kritik Aşırı Şişkinlik (RSI={rsi:.1f})"
            else:
                reason = "Negatif MACD kesişimi ve satıcı baskısı"
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
                reason = "Piyasa yatay konsolidasyon evresinde (Kırılım bekleniyor)"
            else:
                reason = "İndikatörler uyumsuz, net teyit bekleniyor"
            
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
        
        # KULLANICI İSTEĞİ: Yüksekten (zaten patlamış) varlıkları değil, dipten toparlanan veya yeni harekete başlayan (RSI 25-50) varlıkları yarıştır!
        chg_val = m.get("change_pct", 0.0)
        rsi_val = m.get("rsi", 50.0)
        
        chg_bonus = 0.0
        if chg_val > 6.0:
            chg_bonus = -10.0 # Zaten patlamış, trene sondan binme cezası
        elif 0.5 <= chg_val <= 3.5:
            chg_bonus = +5.0  # Yeni uyanıyor, patlamaya hazır (Erken trend)
            
        rsi_bonus = 0.0
        if 25.0 <= rsi_val <= 35.0:
            rsi_bonus = +8.0  # Aşırı satım, dip fiyat!
        elif 35.0 < rsi_val <= 50.0:
            rsi_bonus = +4.0  # Dipten dönüş, yükseliş potansiyeli
        elif rsi_val >= 75.0:
            rsi_bonus = -10.0 # Şişmiş, riskli bölge
            
        # Temel indikatör skoru + Kullanıcı felsefesine (Erken Keşif) uygun bonuslar
        # Eskiden burası (score * 2.5) ile aşırı şişiyordu. Şimdi 2.0 yaptık.
        base_ind_score = min(40.0, (m.get("score", 0) * 2.0) + chg_bonus + rsi_bonus)
        
        m["expertise_level"] = ai_data.get("expertise_level", "🟡 NÖTR / DENGELİ")
        m["ai_action"] = ai_data.get("action_recommendation", "🟡 Standart İnceleme")
        
        # Teknik yarış taban skoru (Eskiden 35'ti. Şişmeyi önlemek için 25'e çektik)
        final_dynamic_score = 25.0 + base_ind_score
        
        # ML / AI Geçmiş Deneyimi (Experience Memory Engine)
        historical_sample = int(ai_data.get("total_trades", 0) or 0) if ai_data else 0
        if ai_data and "confidence_score" in ai_data:
            raw_conf = float(ai_data["confidence_score"])
            sample_factor = min(1.0, historical_sample / 10.0)
            
            # ML'in Geçmiş Tecrübe Skoru
            ai_bonus = (raw_conf - 50.0) * 0.3 * sample_factor 
            
            if raw_conf >= 75.0 and sample_factor >= 0.5:
                ai_bonus += 5.0 # Eskiden 10'du, şişmeyi önlemek için düşürüldü
            
            ai_bonus = min(15.0, max(-15.0, ai_bonus))
            final_dynamic_score += ai_bonus
            
            if ai_bonus > 3.0:
                m["reason"] += f" | 🧠 ML Geçmişi Parlak (+{ai_bonus:.1f} Puan)"
            elif ai_bonus < -3.0:
                m["reason"] += f" | 🧠 ML Sabıkalı Varlık ({ai_bonus:.1f} Puan)"
            
        # Aksiyon Boost KALDIRILDI (Çünkü zaten "BUY" kararı Score üzerinden alınıyordu, çifte puanlama yapıyordu)
        
        # Hacim Boost: Maksimum +8, Minimum -3
        vol_ratio_val = m.get("volume_ratio", 1.0) or 1.0
        volume_boost = min(8.0, max(-3.0, (vol_ratio_val - 1.0) * 3.5))
        
        # 💣 Ticking Time Bomb (Patlamaya Hazır Bomba) Sıkışma Bonusu
        squeeze_bonus = 0.0
        current_rsi = m.get("rsi", 50.0)
        current_adx = float(m.get("adx", 0.0) or 0.0)
        # Sıkışma (Konsolidasyon) Şartları: RSI 40-55 arası (ne aşırı satım ne aşırı alım), trend yatay (ADX < 25)
        is_consolidating = (40.0 <= current_rsi <= 55.0) and (current_adx < 25.0)
        
        if is_consolidating and vol_ratio_val > 1.8:
            # Sıkışan bir tahtaya aniden devasa hacim (1.8x) girdiyse, bu bir patlama sinyalidir!
            squeeze_bonus = 15.0
            m["reason"] = f"🧨 SIKIŞMA KIRILIMI: Patlamaya hazır bomba! Hacim {vol_ratio_val:.1f}x"
            m["badge"] = "🧨 BOMBA"
        elif is_consolidating and vol_ratio_val > 1.3:
            # Hafif uyanış
            squeeze_bonus = 7.0
            m["reason"] += " | 🧨 Uyanış (Hacim artıyor)"
        
        # Adil Değer (Fair Value) Hesaplaması
        fair_value_boost = 0.0
        session_high = m.get("high", price * 1.02)
        session_low = m.get("low", price * 0.98)
        
        if session_high > session_low:
            position_in_range = (price - session_low) / (session_high - session_low)
            
            if position_in_range <= 0.30:
                fair_value_boost = 6.0
                dist_from_low = max(0, ((price - session_low) / session_low) * 100)
                m["reason"] += f" | 📉 Adil Değer Altı (Dibe %{dist_from_low:.1f} Yakın)"
            elif position_in_range >= 0.75:
                fair_value_boost = -5.0
                dist_from_high = max(0, ((session_high - price) / price) * 100)
                if dist_from_high < 0.05:
                    m["reason"] += f" | 📈 Zirve Testi"
                else:
                    m["reason"] += f" | 📈 Zirve Fiyatlama"
                
        final_dynamic_score += (volume_boost + squeeze_bonus + fair_value_boost)
        
        # --- SAF MATEMATİKSEL HACİM VE MOMENTUM ÇARPANLARI ---
        current_rsi = m.get("rsi", 50.0)
        current_vol = m.get("volume_ratio", 1.0) or 1.0
        
        # Hacim artışına göre orantısal puan (Maksimum +5 puan) - Sadece hacim > 2.0 ise etki eder.
        if current_vol >= 2.0:
            vol_bonus = min(5.0, (current_vol - 1.0) * 1.5)
            final_dynamic_score += vol_bonus
            
        # Düşük hacim ve yataylık cezası
        if 45.0 <= current_rsi <= 55.0 and current_vol < 0.8:
            final_dynamic_score -= 5.0
        
        # ─── GÜVEN SKORU: Geniş Marjlı Doğal Dağılım ───────────────────────────
        quality_factor = 0.90 + (0.10 * float(m.get("indicator_coverage", 0.0)))
        
        # Otonom Konsey Kararı: Yarış dinamiklerini yansıtmak için taban skor (baseline) 30'dan 45'e çekildi.
        ranking_score = min(99.0, max(1.0, round(final_dynamic_score, 1)))
        confidence_score = round(45.0 + (ranking_score - 30.0) * quality_factor, 1)
        
        # Sadece KESİN ve ÇOK GÜÇLÜ hisseler 90 üzerine çıkabilsin diye hafif bir ceza (eskisi kadar pısırık değil):
        if confidence_score > 85.0:
            confidence_score = 85.0 + ((confidence_score - 85.0) * 0.8) # 85'ten sonrasını hafif frenle
            
        # Son 30 dk yarış verisi çarpanı (Simülasyon/Geçmiş ağırlığı)
        # Hacim ve Trend güçlü olan varlıklar doğrudan zirve yarışına girer.
        confidence_score = min(99.9, max(0.0, round(confidence_score, 1)))
        
        if m.get("decision_gate") != "ALLOW_ENTRY":
            ranking_score = 0.0
            confidence_score = 0.0
            
        # === Puan Yumuşatma (Smoothing / EMA) ===
        now_ts = time.time()
        if sym not in _score_history:
            _score_history[sym] = []
            
        # Sadece son 15 dakikadaki (900 saniye) kayıtları tut - TUTARLI VE YUMUŞAK GEÇİŞ
        _score_history[sym].append((now_ts, confidence_score, ranking_score))
        _score_history[sym] = [t for t in _score_history[sym] if now_ts - t[0] <= 900]
        
        if len(_score_history[sym]) > 1:
            total_weight = 0
            weighted_conf = 0
            weighted_rank = 0
            for t_ts, t_conf, t_rank in _score_history[sym]:
                # Yeni verilere daha fazla ağırlık ver (zaman farkı 0 ise weight 1, 180s ise weight 1/2)
                # Bu sayede 1 dakikalık sahte balina iğneleri listeyi darmadağın edemez, istikrar gerekir.
                weight = 1.0 / (1.0 + (now_ts - t_ts) / 180.0)
                weighted_conf += t_conf * weight
                weighted_rank += t_rank * weight
                total_weight += weight
            confidence_score = round(weighted_conf / total_weight, 1)
            ranking_score = round(weighted_rank / total_weight, 1)

        m["ranking_score"] = ranking_score
        m["confidence_score"] = confidence_score
        m["confidence_label"] = (
            "DATA_BLOCKED" if m.get("decision_gate") != "ALLOW_ENTRY" else
            "HIGH_EVIDENCE" if m["indicator_coverage"] >= 0.83 and historical_sample >= 20
            else "LIVE_TECHNICAL" if m["indicator_coverage"] >= 0.83
            else "PARTIAL_DATA"
        )
        m["historical_sample"] = historical_sample

    grouped_matrix = {
        "CRYPTO": sorted([m for m in matrix_results if m["market"] == "CRYPTO"], key=lambda x: x["confidence_score"], reverse=True)[:50],
        "BIST": sorted([m for m in matrix_results if m["market"] == "BIST"], key=lambda x: x["confidence_score"], reverse=True)[:15],
        "NASDAQ": sorted([m for m in matrix_results if m["market"] == "NASDAQ"], key=lambda x: x["confidence_score"], reverse=True)[:50]
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

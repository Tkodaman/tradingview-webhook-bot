import time
from fastapi import APIRouter
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from services.risk_engine.market_hours import market_hours_validator
from services.market_feed.live_stream import live_trade_manager
from services.risk_engine.fakeout_guard import fakeout_guard

router = APIRouter()
rsi_history = {}

# Kisa cache — karar matrix'i dashboard'da stale görünmesin.
_matrix_cache = {"data": None, "ts": 0}
_CACHE_TTL = 5  # saniye


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
    now = time.time()
    if _matrix_cache["data"] is not None and (now - _matrix_cache["ts"]) < _CACHE_TTL:
        return _matrix_cache["data"]

    live_data = tradingview_live_client.fetch_live_market_data()

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
            
        if open_pos:
            decision = "HOLD"
            badge = "🟢 POSITION_OPEN"
            reason = f"Açık Pozisyon Aktif (Giriş: ${open_pos.entry_price}, PnL: ${open_pos.unrealized_pnl})"
        elif risk_block_reason:
            decision = "WAIT"
            badge = "🚧 RISK_BLOCK"
            reason = risk_block_reason
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
        elif rsi_climbed_from_40:
            decision = "BUY"
            badge = "🟢 BUY_OPPORTUNITY"
            reason = f"Fırsat: RSI 40-50 bölgesinden ivmelenerek {rsi:.1f} bandını geçti"
        elif score >= 3:
            decision = "BUY"
            badge = "🟢 BUY_SIGNAL"
            
            adx_val = _number(data.get("adx"), 0.0)
            if data.get("vwap_bullish", False) and vol_ratio >= 1.0:
                reason = "Fiyat VWAP üstünde - kurumsal destek aktif"
            elif data.get("ema_golden_cross", False):
                reason = "EMA Golden Cross aktif (20>50>200)"
            elif adx_val >= 40:
                reason = f"Güçlü trend ivmesi ADX={int(adx_val)}"
            elif rsi < 40 and macd > 0:
                reason = "Aşırı satım dibinden MACD alım kesişimi"
            else:
                factors = []
                if rsi > 60: factors.append(f"RSI({rsi:.1f}) Güçlü")
                elif rsi > 50: factors.append("RSI Pozitif")
                if macd > 0: factors.append("MACD Alışta")
                if vol_ratio > 1.2: factors.append(f"Hacim Sıçraması({vol_ratio:.1f}x)")
                if chg > 1.0: factors.append("Fiyat İvmeli")
                if 20.0 <= stoch_k <= 85.0: factors.append("Stoch Teyitli")
                if cmf > 0.05: factors.append("Kurumsal Toplama (CMF)")
                
                if len(factors) >= 2:
                    reason = " | ".join(factors[:2]) + f" ({score}/9)"
                elif len(factors) == 1:
                    reason = factors[0] + f" | Eğilim Pozitif ({score}/9)"
                else:
                    reason = f"Teknik Görünüm İyileşiyor ({score}/9)"
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
        
        # Temel indikatör ve ivme bazlı puan — her indikatör adil yarışır
        # Skor şişmesini engellemek için katsayı 3.0'a çekildi (max ~50)
        base_ind_score = min(50.0, (m.get("score", 0) * 3.0) + (m.get("change_pct", 0.0) * 1.0))
        
        m["expertise_level"] = ai_data.get("expertise_level", "🟡 NÖTR / DENGELİ")
        m["ai_action"] = ai_data.get("action_recommendation", "🟡 Standart İnceleme")
        
        # Teknik yarış skoru. Sabit 40 taban puanı yok; eksik veri avantaj üretmez.
        final_dynamic_score = 35.0 + base_ind_score
        
        # AI Geçmişi BONUS olarak ekleniyor (katsayı değil düz bonus)
        historical_sample = int(ai_data.get("total_trades", 0) or 0) if ai_data else 0
        if ai_data and "confidence_score" in ai_data:
            raw_conf = float(ai_data["confidence_score"])
            # Küçük örneklem geçmişi teknik skoru domine edemez.
            sample_factor = min(1.0, historical_sample / 20.0)
            ai_bonus = min(5.0, max(-3.0, (raw_conf - 50.0) * 0.12 * sample_factor))
            final_dynamic_score += ai_bonus
            
        # Aksiyon Boost (Al sinyali güçlü, Sat sinyali düşür)
        action_boost = 0.0
        if "BUY" in m["decision"] or "AL" in m["ai_action"].upper():
            action_boost = 5.0
        elif "SELL" in m["decision"] or "SAT" in m["ai_action"].upper():
            action_boost = -5.0
            
        # Hacim Boost: 1.0x'ten sapma kadar ek puan (max +8, min -3)
        vol_ratio_val = m.get("volume_ratio", 1.0) or 1.0
        volume_boost = min(8.0, max(-3.0, (vol_ratio_val - 1.0) * 4.0))
        
        # Adil Değer (Fair Value) Hesaplaması — orta banda ceza YOK
        fair_value_boost = 0.0
        session_high = m.get("high", price * 1.02)
        session_low = m.get("low", price * 0.98)
        
        if session_high > session_low:
            position_in_range = (price - session_low) / (session_high - session_low)
            
            if position_in_range <= 0.30:
                # Güne dipte işlem görüyor → Fırsat (Eşiği 0.25'ten 0.30'a çektim biraz daha esnek olsun)
                fair_value_boost = 6.0
                dist_from_low = max(0, ((price - session_low) / session_low) * 100)
                m["reason"] += f" | 📉 Adil Değer Altı (Dibe %{dist_from_low:.1f} Yakın)"
            elif position_in_range >= 0.75:
                # Güne zirvede işlem görüyor → Risk (0.80'den 0.75'e çektim)
                fair_value_boost = -5.0
                dist_from_high = max(0, ((session_high - price) / price) * 100)
                if dist_from_high < 0.05:
                    m["reason"] += f" | 📈 Zirve Testi (Gün içi yüksek: ${session_high:.2f}, fiyat zirve seviyesinde)"
                else:
                    m["reason"] += f" | 📈 Zirve Fiyatlama (Gün içi yüksek: ${session_high:.2f}, zirveye %{dist_from_high:.2f} uzak)"
            # Orta bant: nötr, ceza yok
                
        final_dynamic_score += (action_boost + volume_boost + fair_value_boost)
        
        # Yatay / Kararsız Piyasa Cezası (Hafif)
        # RSI 44-56 + düşük hacim = yatay bekleniyor, sadece hafif indir
        current_rsi = m.get("rsi", 50.0)
        current_vol = m.get("volume_ratio", 1.0) or 1.0
        if 44.0 <= current_rsi <= 56.0 and current_vol < 0.8:
            final_dynamic_score -= 8.0  # Eskisi -20, artık hafif -8
            m["reason"] += " (Yatay Bölge/Düşük Hacim)"
        
        # ─── GÜVEN SKORU: Geniş Marjlı Doğal Dağılım ───────────────────────────
        # Formül: 50 + (ranking - 50) * quality_factor
        # Bu formül 50 etrafında simetrik, doğal bir dağılım üretir:
        #   WAIT sinyal  (final~45)  → ~45%
        #   Zayıf BUY   (final~58)  → ~58%
        #   Orta BUY    (final~67)  → ~67%
        #   Güçlü BUY   (final~85)  → ~84%  (otonom eşiğe yakın)
        #   Çok Güçlü   (final~98)  → ~97%  (otonom tetikler!)
        #
        # Eski sorun: quality_factor min=0.65 → final=85 iken conf=72.75 (daralma)
        # Düzeltme:   quality_factor min=0.92 → final=85 iken conf=84.5  (doğru!)
        
        quality_factor = 0.92 + (0.08 * float(m.get("indicator_coverage", 0.0)))
        # quality_factor: min 0.92 (eksik veri), max 1.00 (tam veri)
        
        ranking_score = min(99.9, max(1.0, round(final_dynamic_score, 1)))
        confidence_score = round(50.0 + (ranking_score - 50.0) * quality_factor, 1)
        confidence_score = min(99.9, max(0.0, confidence_score))
        
        if m.get("decision_gate") != "ALLOW_ENTRY":
            ranking_score = 0.0
            confidence_score = 0.0
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
        "CRYPTO": sorted([m for m in matrix_results if m["market"] == "CRYPTO"], key=lambda x: x["confidence_score"], reverse=True)[:15],
        "BIST": sorted([m for m in matrix_results if m["market"] == "BIST"], key=lambda x: x["confidence_score"], reverse=True)[:15],
        "NASDAQ": sorted([m for m in matrix_results if m["market"] == "NASDAQ"], key=lambda x: x["confidence_score"], reverse=True)[:50]
    }
        
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
    live_data = tradingview_live_client.fetch_live_market_data()
    
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

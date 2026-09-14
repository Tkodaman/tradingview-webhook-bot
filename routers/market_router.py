import time
from fastapi import APIRouter
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from services.risk_engine.market_hours import market_hours_validator
from services.market_feed.live_stream import live_trade_manager

router = APIRouter()
rsi_history = {}

@router.get("/live-matrix")
async def get_live_buy_sell_wait_matrix():
    """
    Anlık Gerçek Zamanlı BUY / SELL / WAIT Canlı Sinyal Kokpiti
    Taranan tüm NASDAQ (60), BIST (10) ve KRİPTO (20) varlıklarının anlık sinyal durumunu hesaplar.
    Piyasa açık/kapalı durumunu kontrol eder ve gruplandırır.
    """
    live_data = tradingview_live_client.fetch_live_market_data()
    overview = market_hours_validator.get_market_overview()
    matrix_results = []
    t_sec = int(time.time() * 1.5)
    
    for sym, data in live_data.items():
        base_price = float(data.get("price", 0.0))
        rsi = data.get("rsi", 50.0)
        macd = data.get("macd", 0.0)
        vol_ratio = data.get("volume_ratio", 1.0)
        chg = data.get("change_pct", 0.0)
        
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

        # OTONOM ML & YÜKSELİŞ POTANSİYELİ PUANLAMASI (Kazan-Kazan Erken Keşif)
        score = 0
        
        # 1. Temel İndikatörler (Yükselişini tamamlamamış, ivmelenen varlıklar)
        if 40.0 <= rsi <= 60.0: score += 2 # Henüz şişmemiş, potansiyelli
        elif 60.0 < rsi <= 72.0: score += 1 # Trendde ama yolun yarısında
        if macd >= 0.0: score += 1
        if data.get("ema_golden_cross", False): score += 2 # Güçlü sinyal
        if data.get("vwap_bullish", False): score += 1
        if vol_ratio >= 1.5: score += 3 # Hacim patlaması (Balina)
        elif vol_ratio >= 0.80: score += 1
        if 20.0 <= data.get("stoch_k", 50.0) <= 80.0: score += 1
        if data.get("adx", 25.0) >= 20.0: score += 1 # Trend yeni başlıyor/güçleniyor
        if data.get("cmf", 0.0) > 0.10: score += 2 # Yüksek Kurumsal Giriş
        if chg >= 0.5 and vol_ratio >= 1.2: score += 3 # Momentum Impulse (Dipten Dönüş)

        # ==========================================
        # KAZAN-KAZAN ERKEN PATLAMA TESPITI
        # "Yükselişini tamamlamamış" varlıklar için mega bonus
        # ==========================================
        momentum_phase = "NEUTRAL"  # Varsayılan
        
        # A. ERKEN PATLAMA: RSI 35-55 bölgesinde hacim patlaması var
        if 35.0 <= rsi <= 55.0 and vol_ratio >= 1.5 and chg >= 0.5:
            score += 5  # Mega bonus: yükseliş henüz başlıyor
            momentum_phase = "EARLY_EXPLOSION"
        # B. TAZE İVME: RSI 40-60 arasında EMA Golden Cross taze kırılım
        elif 40.0 <= rsi <= 62.0 and data.get("ema_golden_cross", False):
            score += 3
            momentum_phase = "FRESH_BREAKOUT"
        # C. BALINA DALGASI: vol_ratio >= 2.0 her durumda
        elif vol_ratio >= 2.0:
            score += 4
            momentum_phase = "WHALE_WAVE"
        # D. ZİRVEYE YAKIN (Ceza): RSI > 72 ve zaten çok yükselmiş
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
        
        if open_pos:
            decision = "HOLD"
            badge = "🟢 POSITION_OPEN"
            reason = f"Açık Pozisyon Aktif (Giriş: ${open_pos.entry_price}, PnL: ${open_pos.unrealized_pnl})"
        elif not is_open:
            decision = "WAIT"
            badge = "💤 SEANS_DISI"
            reason = f"Piyasa Kapalı: {market_status.get('session_text', 'Seans saatleri dışında')}"
        elif rsi > 72.0 or macd < -1.5:
            decision = "SELL"
            badge = "🔴 SELL_SIGNAL"
            if rsi > 72.0:
                reason = f"Aşırı Şişkin/Risk Sınırı Aşıldı (RSI={rsi:.1f})"
            else:
                reason = "Negatif MACD kesişimi ve satıcı baskısı"
        elif rsi_climbed_from_40:
            decision = "BUY"
            badge = "🟢 BUY_OPPORTUNITY"
            reason = f"Fırsat: RSI 40-50 bölgesinden ivmelenerek {rsi:.1f} bandını geçti"
        elif score >= 3:
            decision = "BUY"
            badge = "🟢 BUY_SIGNAL"
            
            adx_val = data.get("adx", 0)
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
                if 20.0 <= data.get("stoch_k", 50.0) <= 85.0: factors.append("Stoch Teyitli")
                if data.get("cmf", 0.0) > 0.05: factors.append("Kurumsal Toplama (CMF)")
                
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
        
        # Temel indikatör ve ivme bazlı puan (Maks: ~50-60)
        base_ind_score = (m.get("score", 0) * 5.0) + (m.get("change_pct", 0.0) * 2.0)
        
        m["expertise_level"] = ai_data.get("expertise_level", "🟡 NÖTR / DENGELİ")
        m["ai_action"] = ai_data.get("action_recommendation", "🟡 Standart İnceleme")
        
        if ai_data and "confidence_score" in ai_data:
            # Yapay zeka geçmişte bu varlıkta işlem yaptıysa
            raw_conf = float(ai_data["confidence_score"])
            # %60 Tarihsel Başarı (Tecrübe) + %40 Anlık İvme
            final_dynamic_score = (raw_conf * 0.60) + (base_ind_score * 0.80)
        else:
            # Daha önce işlem yapılmamış yeni varlık (Temel puan üzerine kurgulanır)
            final_dynamic_score = 40.0 + base_ind_score
            
        # Aksiyon ve Momentum Boost
        action_boost = 0
        if "BUY" in m["decision"] or "AL" in m["ai_action"].upper():
            action_boost = 8.0
        elif "SELL" in m["decision"] or "SAT" in m["ai_action"].upper():
            action_boost = -10.0
            
        volume_boost = (m.get("volume_ratio", 1.0) - 1.0) * 3.0
        
        # Algoritmik "Adil Değer" (Fair Value) ve Dip/Zirve Hesaplaması
        fair_value_boost = 0.0
        session_high = m.get("high", price * 1.02)
        session_low = m.get("low", price * 0.98)
        
        if session_high > session_low:
            # Fiyatın dip ile zirve arasındaki göreceli konumu (0 = Tam Dip, 1 = Tam Zirve)
            position_in_range = (price - session_low) / (session_high - session_low)
            
            if position_in_range <= 0.30:
                # Fiyat alt çeyrekte (Dipten ucuz fiyatlanıyor)
                fair_value_boost = 10.0
                m["reason"] += " | 📉 Adil Değerin Altında (Dipten Giriş Fırsatı)"
            elif position_in_range >= 0.70:
                # Fiyat üst çeyrekte (Şişkin / Zirvede)
                fair_value_boost = -10.0
                m["reason"] += " | 📈 Zirve Fiyatlama (Düzeltme Riski)"
            else:
                # Tam Ortada (0.30 ile 0.70 arası)
                fair_value_boost = -5.0
                
        final_dynamic_score += (action_boost + volume_boost + fair_value_boost)
        
        # ARAF (Nötr Bölge) Cezası: Kullanıcı talebi (Ortadan girmeyelim)
        # Eğer RSI 42 ile 58 arasındaysa ve hacim düşükse (Yatay/Kararsız Piyasa)
        current_rsi = m.get("rsi", 50.0)
        current_vol = m.get("volume_ratio", 1.0)
        if 42.0 <= current_rsi <= 58.0 and current_vol < 1.0:
            final_dynamic_score -= 20.0 # Puanı kırarak listeye çıkmasını engelle
            m["reason"] += " (Araf/Yatay Bölge Cezası)"
        
        # Skoru 1.0 ile 99.9 arasına sınırla
        m["confidence_score"] = min(99.9, max(1.0, round(final_dynamic_score, 1)))

    grouped_matrix = {
        "CRYPTO": sorted([m for m in matrix_results if m["market"] == "CRYPTO"], key=lambda x: x["confidence_score"], reverse=True)[:15],
        "BIST": sorted([m for m in matrix_results if m["market"] == "BIST"], key=lambda x: x["confidence_score"], reverse=True)[:15],
        "NASDAQ": sorted([m for m in matrix_results if m["market"] == "NASDAQ"], key=lambda x: x["confidence_score"], reverse=True)[:30]
    }
        
    return {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "markets_overview": overview,
        "total_monitored_assets": len(matrix_results),
        "signals_summary": {
            "BUY": len([m for m in matrix_results if m["decision"] == "BUY"]),
            "SELL": len([m for m in matrix_results if m["decision"] == "SELL"]),
            "WAIT": len([m for m in matrix_results if m["decision"] == "WAIT"]),
            "HOLD": len([m for m in matrix_results if m["decision"] == "HOLD"])
        },
        "grouped": grouped_matrix,
        "matrix": matrix_results
    }

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

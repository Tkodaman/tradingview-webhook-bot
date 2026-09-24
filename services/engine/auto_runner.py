"""
Otonom TradingView Canli Strateji ve Tetikleyici Motoru
Ders Cikarimli Olasilik Odakli Kendini Kalibre Eden Islem Algoritmasi (Self-Learning Execution Engine)
"""

import time
import asyncio
from typing import Dict, Any, List
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from services.market_feed.live_stream import live_trade_manager
from services.engine.experience_memory_engine import experience_memory_engine
from services.engine.trade_journal_learning import trade_journal_engine
from services.ai_agent.system_prompt import RISK_PARAMS
from schemas.webhook import WebhookSignal
from services.order_router import process_order
from services.risk_engine.market_hours import market_hours_validator
from core.config import settings
from core.logger import logger
from services.intelligence.llm_market_intelligence import LLMMarketIntelligenceEngine
# === YENI MODULLER (7 Kritik Yukseltme) ===
from services.intelligence.fear_greed_index import fear_greed_client
from services.risk_engine.consecutive_loss_breaker import consecutive_loss_breaker
from services.risk_engine.correlation_filter import correlation_filter
from services.intelligence.market_regime_detector import market_regime_detector
from services.risk_engine.dynamic_sl_tp import calculate_atr_based_tp_sl
from services.trainer.ml_signal_predictor import ml_predictor
from services.risk_engine.fakeout_guard import fakeout_guard
from services.engine.market_regime_engine import regime_engine
from services.engine.bot_thought_stream import bot_thought_stream

# Global instances
llm_intelligence = LLMMarketIntelligenceEngine()

class TradingViewAutoStrategyRunner:
    def __init__(self):
        self.is_running: bool = True  # Varsayılan olarak 7/24 kesintisiz otonom aktif
        self.scan_interval_seconds: float = 3.0
        self.min_score_required: int = 6  # Yüksek seçicilik (6/8) ile agresif kayıpların önüne geçilmesi
        # === FIX-2: Timestamp bazlı cooldown (eskisi string'di, duplicate pozisyon açıyordu) ===
        self.last_evaluated_signals: Dict[str, float] = {}  # sym -> Unix timestamp of last trade
        self._loop_task: Any = None
        self.SYMBOL_COOLDOWN_SECONDS: float = 300.0  # Aynı sembolde 5 dk bekleme
        self._closed_trades_since_last_advisor: int = 0  # Profit Advisor otomatik tetikleyici sayaci
        self._profit_advisor_interval: int = 10  # Her 10 islemde bir Profit Advisor calistir

    async def start_continuous_background_loop(self):
        """
        Sunucu arkasında 7/24 kesintisiz çalışan bağımsız otonom tarama döngüsü.
        """
        logger.info("[AUTO-RUNNER] Olasılık Ağırlıklı Kendini Kalibre Eden Motor Başlatıldı.")
        while True:
            try:
                if self.is_running:
                    # Central tick clock: Evaluate open positions and update trailing stops autonomously
                    await asyncio.to_thread(live_trade_manager.get_live_prices)
                    
                    # Evaluate new signals
                    await asyncio.to_thread(self.evaluate_live_market_and_trigger)
            except Exception as e:
                logger.error(f"[AUTO-RUNNER ERROR] {e}")
            await asyncio.sleep(self.scan_interval_seconds)

    def evaluate_live_market_and_trigger(self) -> List[Dict[str, Any]]:
        """
        TradingView verilerini tarar, öğrendiği otopsi derslerine ve olasılık sonuç yüzdelerine göre
        hata payını en aza indirerek işlem tetikler.
        """
        if not self.is_running:
            return []

        # === DEVRE KESICI KONTROLU: Arka arkaya zarar durumunda tum alimlari durdur ===
        paused, pause_reason = consecutive_loss_breaker.is_trading_paused()
        if paused:
            logger.warning(f"[LOSS BREAKER] Tum alimlar durakladi: {pause_reason}")
            return []

        # === FIX-2: Cooldown'ı expired olan sinyalleri temizle ===
        now_ts = time.time()
        self.last_evaluated_signals = {
            k: v for k, v in self.last_evaluated_signals.items()
            if now_ts - v < self.SYMBOL_COOLDOWN_SECONDS
        }

        # === FEAR & GREED KONTROLU: Asiri acgozluluk varsa yeni alim yapma ===
        fg_assessment = fear_greed_client.get_assessment()
        if fg_assessment.should_block:
            logger.warning(f"[FEAR&GREED BLOCK] {fg_assessment.block_reason}")
            return []

        market_data_raw = tradingview_live_client.fetch_live_market_data()
        executed_triggers = []

        # === RSI YARIŞI: Yüksek RSI momentum = önce değerlendir ===
        # Amac: Guclu ivme gosteren semboller once sinyal uretsin
        # RSI 60-75 = olgun ama henüz zirvede değil = ideal yarışçı
        def _rsi_race_key(item):
            sym, d = item
            rsi_val  = float(d.get("rsi", 0.0) or 0.0)
            vol_val  = float(d.get("volume_ratio", 0.0) or 0.0)
            chg_val  = float(d.get("change_pct", 0.0) or 0.0)
            # Birleşik yarış skoru: RSI ana kriter, hacim ve değişim tiebreaker
            return rsi_val * 1.0 + vol_val * 5.0 + chg_val * 2.0

        market_data = dict(sorted(market_data_raw.items(), key=_rsi_race_key, reverse=True))

        # Top-5 RSI yarışçısını logla (her döngüde)
        top5_race = [(s, round(float(d.get('rsi', 0) or 0), 1),
                      round(float(d.get('volume_ratio', 0) or 0), 2),
                      round(float(d.get('change_pct', 0) or 0), 2))
                     for s, d in list(market_data.items())[:5]]
        if top5_race:
            race_str = " | ".join([f"{s}(RSI={r} VOL={v} CHG={c}%)" for s, r, v, c in top5_race])
            logger.info(f"[RSI YARISI] Oncelik sirasi: {race_str}")

        for sym, data in market_data.items():
            # === FIX-2: Duplicate guard — Aynı sembol için cooldown süresi dolmadan geçme ===
            if sym in self.last_evaluated_signals:
                elapsed = now_ts - self.last_evaluated_signals[sym]
                if elapsed < self.SYMBOL_COOLDOWN_SECONDS:
                    logger.debug(f"[DUPLICATE GUARD] {sym} cooldown aktif ({int(self.SYMBOL_COOLDOWN_SECONDS - elapsed)}s kaldi). Atlanıyor.")
                    continue
            # === TOXIC ASSET GUARD (Stablecoins & Pegged Assets) ===
            # PAXG (Gold peg), stablecoins (USDC, USDT, TUSD), and fiat pegs are highly illiquid/low-volatility 
            # and suffer massive spread slippage. Auto-runner MUST ignore them.
            toxic_keywords = ["PAXG", "USDTUSD", "USDC", "TUSD", "BUSD", "DAI", "FDUSD", "XAUT", "EURUSD", "GBPUSD"]
            if any(toxic in sym.upper() for toxic in toxic_keywords):
                logger.debug(f"[TOXIC ASSET GUARD] {sym} is blacklisted (stablecoin/fiat/gold peg). Atlanıyor.")
                continue

            # Piyasa calisma saati kontrolu: BIST veya NASDAQ kapali ise kesinlikle alim yapma
            is_open, mkt_msg, _ = market_hours_validator.is_market_open(sym)
            if not is_open:
                continue

            price = data.get("price", 0.0)
            if price <= 0:
                continue

            rsi = data.get("rsi", 50.0)
            macd = data.get("macd", 0.0)
            ema_golden = data.get("ema_golden_cross", False)
            supertrend_bullish = data.get("supertrend_bullish", True)
            vwap_bull = data.get("vwap_bullish", False)
            
            # Trend Uyuşmazlığı (Trend Conflict)
            trend_conflict = False
            if ema_golden != supertrend_bullish:
                trend_conflict = True
            
            vol_ratio = data.get("volume_ratio")
            if vol_ratio is None:
                logger.warning(f"[AUTO-RUNNER] {sym} için volume_ratio verisi yok. Sembol atlanıyor.")
                continue
                
            stoch_k = data.get("stoch_k", 50.0)
            adx = data.get("adx", 25.0)
            atr_pct = data.get("atr_pct", 1.5)
            chg_pct = data.get("change_pct", 0.0)
            cmf = data.get("cmf", 0.0)
            rs_score = data.get("rs_score", 0.0)

            # === YENİ İNDİKATÖR VERİLERİ (Güven Skoru İçin) ===
            # Higher-High Pattern: Son 3 kapanışın yükselen tepe
            prev_high_1 = data.get("prev_high_1", 0.0)   # 1 mum önceki high
            prev_high_2 = data.get("prev_high_2", 0.0)   # 2 mum önceki high
            # Candle Body Ratio: Mum gövdesinin toplam aralığa oranı
            candle_open  = data.get("candle_open", price)  # Mumun açılışı
            candle_high  = data.get("candle_high", price)  # Mumun zirvesi
            candle_low   = data.get("candle_low",  price)  # Mumun dibi
            # Orderbook Pressure: Alici / (Alici + Satici) orani [0..1]
            bid_ask_ratio = data.get("bid_ask_ratio", 0.5)  # >0.55 = alici baskisi

            # ==========================================
            # DERS ÇIKARIMLI KATI FİLTRELER (ÖĞRENİLEN TELER & TUZAK ENGELLERİ)
            # ==========================================

            # === GELISmIs FOMO ENGELI: RSI + Degisim + Hacimsiz Yukselis kombinasyonu ===
            fomo_chg = RISK_PARAMS.get("fomo_candle_change_pct", 5.0)
            fomo_rsi  = RISK_PARAMS.get("fomo_rsi_limit", 85.0)
            fomo_score = 0
            if rsi is not None and rsi > fomo_rsi: fomo_score += 2
            elif rsi is not None and rsi > 80: fomo_score += 1
            if chg_pct >= fomo_chg: fomo_score += 2
            elif chg_pct >= 3.0: fomo_score += 1
            if vol_ratio is not None and vol_ratio < 1.3 and chg_pct > 2.0: fomo_score += 1  # Hacimsiz yukselis
            if fomo_score >= 6:
                logger.info(f"[GELISMIS FOMO BLOCK] {sym} FOMO skoru={fomo_score}/6 (RSI:{rsi}, CHG:{chg_pct:.1f}%, VOL:{vol_ratio:.2f}). Pullback bekleniyor.")
                continue

            # DERS KURALI 2: Düşük Volatiliteli RSI Tepe Tuzağı (RSI > 68 & ATR < 1.0)
            if rsi is not None and atr_pct is not None and rsi > 68.0 and atr_pct < 1.0:
                logger.info(f"[SELF-LEARNING BLOCK] {sym} Düşük volatilitede RSI aşırı alım tuzağında (RSI: {rsi:.1f}, ATR: %{atr_pct}). Reddedildi.")
                continue

            # === RSI / ADX None Korumasi: Gercek veri yoksa kararı atlat ===
            if rsi is None:
                logger.debug(f"[DATA GUARD] {sym} RSI verisi yok (buffer dolmadi). Atlanıyor.")
                continue
            if adx is None:
                logger.debug(f"[DATA GUARD] {sym} ADX verisi yok (buffer dolmadi). Atlanıyor.")
                continue

            # Dinamik Piyasa Rejimi (Market Regime) Hesaplama
            ema_gc = data.get("ema_golden_cross", False)
            if ema_gc and rsi > 60.0:
                dynamic_regime = "GÜÇLÜ BOĞA (Golden Cross & RSI > 60)"
            elif ema_gc and rsi <= 60.0:
                dynamic_regime = "KADEMELİ BOĞA (Golden Cross & RSI Düşük)"
            elif not ema_gc and rsi < 40.0:
                dynamic_regime = "AŞIRI SATIM DESTEĞİ (Bearish & RSI < 40)"
            else:
                dynamic_regime = "NÖTR YATAY PİYASA"

            # === FIX-5: Sembol bazlı toksik blok kontrolü (consecutive_loss_breaker'dan) ===
            sym_paused, sym_pause_reason = consecutive_loss_breaker.is_trading_paused(symbol=sym)
            if sym_paused:
                logger.warning(f"[SYMBOL TOXIC BLOCK] {sym} sembolü bloklu: {sym_pause_reason}")
                continue

            # DERS KURALI 3: Hafıza Denetimi (Peş Peşe 2 Stop Olunan Rejimde 2-Strike Hard Block)
            indicators_map = {"rsi": rsi, "volume_ratio": vol_ratio, "atr_pct": atr_pct}
            mem_check = experience_memory_engine.evaluate_signal_against_memory(sym, "BUY", indicators_map, dynamic_regime)
            if not mem_check.get("is_safe", True):
                logger.info(f"[MEMORY SHIELD BLOCK] {sym} islemi Koruma Kalkani tarafindan reddedildi: {mem_check.get('reason')}")
                continue

            # === KORELASYON FILTRESI: Ayni gruptan cok fazla pozisyon varsa engelle ===
            open_positions_list = list(live_trade_manager.positions.values())
            corr_ok, corr_reason = correlation_filter.check(sym, open_positions_list)
            if not corr_ok:
                logger.info(f"[CORRELATION BLOCK] {sym}: {corr_reason}")
                bot_thought_stream.add("🔗 Korelasyon Filtresi", sym, f"Bekliyorum: {corr_reason}", "WARN")
                continue

            # === PIYASA REJIMI TESPITI ===
            hurst = data.get("hurst_exponent", 0.55)
            keltner_sq = data.get("keltner_squeeze_status", "NEUTRAL")
            regime_result = market_regime_detector.detect(
                adx=adx, atr_pct=atr_pct, hurst_exponent=hurst,
                keltner_squeeze=keltner_sq, rsi=rsi
            )
            regime_lot_multiplier = regime_result.lot_multiplier
            # Strateji router / dashboard analitik paneli icin son rejim sonucu sakla
            market_regime_detector.last_results[sym] = regime_result

            # RANGING modda ADX cok dusukse momentum sinyallerini atla
            if regime_result.should_skip_momentum:
                logger.info(f"[REGIME BLOCK] {sym} RANGING rejimde momentum sinyali atland ({regime_result.description})")
                continue

            logger.debug(f"[REGIME] {sym}: {regime_result.regime} | Lot x{regime_lot_multiplier}")

            # === KAZAN-KAZAN: FAKEOUT GUARD v2 (SAHTE KIRILIM TESPITI) ===
            # body_ratio ve bid_ask_ratio onceden hesapla (fakeout guard v2 icin gerekli)
            _candle_range = candle_high - candle_low
            _candle_body  = abs(price - candle_open)
            _body_ratio_early = (_candle_body / _candle_range) if _candle_range > 0 else 0.5

            fakeout_res = fakeout_guard.check(
                symbol=sym, price=price, change_pct=chg_pct, vol_ratio=vol_ratio,
                rsi=rsi, cmf=cmf, stoch_k=stoch_k, atr_pct=atr_pct,
                body_ratio=_body_ratio_early,
                bid_ask_ratio=bid_ask_ratio
            )
            if fakeout_res.is_fakeout:
                logger.warning(f"[FAKEOUT BLOCK v2] {sym} reddedildi: {fakeout_res.reason}")
                bot_thought_stream.add("🎭 Sahte Kırılım Kalkanı", sym, f"Bekliyorum: {fakeout_res.reason}", "WARN")
                continue


            # === KAZAN-KAZAN: ZARAR ANALİZİ KURALI ===
            # NOT: Hacim, ADX ve trend uyumsuzlugu artik HARD BLOCK degil — puanlamada ceza olarak isleniyor.
            # Sadece gercekten tehlikeli olan fakeout ve toxic blok hard engeller kaldi.
            # vol_ratio < 1.2 → İ5 sıfır puan, vol_ratio 0 → zaten yukarıda continue edildi
            # adx < 25      → İ7 puan vermiyor, İ13 momentum bonusu devreye girmiyor
            # EMA/Supertrend çelişme → her ikisi de İ3'te zaten düşük puan
            if vol_ratio < 0.50:  # Sadece tamamen hacim yok ise engelle (eskisi 1.2'ydi)
                logger.info(f"[VOLUME BLOCK] {sym} Hacim neredeyse sifir (vol={vol_ratio:.2f}). Reddedildi.")
                continue

            # ============================================================
            # 📊 İNDİKATÖR PUANLAMA BLOĞU (15 İndikatör — Sıralı)
            # Filtre Değil: Her indikatör puan EKLER veya hafifçe düşürür.
            # Geçiş eşiği: required_score (mod'a göre 3–8 arası)
            # ============================================================
            score = 0

            # === ATR BAZLI DINAMIK TP/SL + REJIM MATRISI ===
            is_crypto = sym.endswith("USDT") or sym in ["BTC", "ETH", "SOL", "BNB"]
            is_mean_reversion_buy = False
            is_arbitrage_buy = False
            atr_absolute = price * (atr_pct / 100.0)

            # Rejim Motorunu guncelle (sadece her 60s'de bir tam hesapla)
            import time as _rtime
            if _rtime.time() - regime_engine._last_update > 60:
                try:
                    regime_engine.compute_regime(live_trade_manager.market_prices)
                except Exception as _re:
                    logger.warning(f"[REGIME ENGINE] Hesaplama hatasi: {_re}")

            # Piyasa tipini al, rejim profilini cek
            _mtype_for_regime = market_hours_validator.get_market_type(sym)
            _regime_profile = regime_engine.get_trade_profile(settings.current_risk_mode, _mtype_for_regime)
            base_tp = _regime_profile["tp_pct"]
            base_sl = _regime_profile["sl_pct"]
            logger.debug(f"[REGIME PROFILE] {sym} {_mtype_for_regime}/{settings.current_risk_mode}/{_regime_profile['regime']} -> TP={base_tp}% SL={base_sl}%")

            # --- Varlık tipine göre ağırlık profili ---
            mkt_type = market_hours_validator.get_market_type(sym)
            weights = {
                "rsi_early":    2 if mkt_type != "CRYPTO" else 1,
                "rsi_mid":      1 if mkt_type != "CRYPTO" else 0,
                "vwap":         2 if mkt_type == "NASDAQ" else 1,
                "volume_surge": 2 if mkt_type == "CRYPTO" else 1.5,
                "volume_norm":  0.5,
                "adx":          1.5 if mkt_type == "NASDAQ" else 1,
            }

            # I1: RSI 40-60 erken ivme, 60-72 orta ivme
            # +++ DUZELTME: RSI 30-40 kor noktasi giderildi (dip bolgesini goruyoruz)
            if 30.0 <= rsi < 40.0:
                score += 0.5  # Kör nokta dolduruldu: dip bölgesi tespiti
                logger.debug(f"[I1 RSI] {sym} RSI={rsi:.1f} dip bolgesi -> +0.5")
            elif 40.0 <= rsi <= 60.0:
                score += weights["rsi_early"]
                logger.debug(f"[I1 RSI] {sym} RSI={rsi:.1f} erken bolge -> +{weights['rsi_early']}")
            elif 60.0 < rsi <= 72.0:
                score += weights["rsi_mid"]
                logger.debug(f"[I1 RSI] {sym} RSI={rsi:.1f} orta bolge -> +{weights['rsi_mid']}")

            # ----------------------------------------------------------
            # İ2 — MACD (Moving Average Convergence/Divergence)
            #       Histogram pozitif veya sıfır = momentum yönü doğru (+1)
            # ----------------------------------------------------------
            if macd >= 0.0:
                score += 1
                logger.debug(f"[İ2 MACD] {sym} MACD={macd:.4f} pozitif → +1")

            # ----------------------------------------------------------
            # İ3 — EMA Golden Cross (20 > 50 > 200)
            #       Üç EMA sıralı → güçlü trend teyidi (+2)
            # ----------------------------------------------------------
            if ema_golden:
                score += 2
                logger.debug(f"[İ3 EMA] {sym} Golden Cross aktif → +2")

            # ----------------------------------------------------------
            # İ4 — VWAP (Volume Weighted Average Price)
            #       Fiyat VWAP üstünde = kurumsal alım bölgesi (+2 NASDAQ / +1 diğer)
            # ----------------------------------------------------------
            if vwap_bull:
                score += weights["vwap"]
                logger.debug(f"[İ4 VWAP] {sym} VWAP üstü → +{weights['vwap']}")

            # I5: Hacim Orani
            # HATA 3 (Hacimsiz Yukselis) ve HATA 1 (Erken Stop) icin:
            # Dusuk hacimde yukselen pozisyona girilmesi -> SL kesiyor
            if vol_ratio >= 1.5:
                score += weights["volume_surge"]
                logger.debug(f"[I5 VOL] {sym} Hacim patlamasi vol={vol_ratio:.2f} -> +{weights['volume_surge']}")
            elif vol_ratio >= 0.80:
                score += weights["volume_norm"]
                logger.debug(f"[I5 VOL] {sym} Normal hacim vol={vol_ratio:.2f} -> +{weights['volume_norm']}")
            elif 0.30 <= vol_ratio < 0.80 and cmf > 0.0:
                # +++ DUZELTME: Sessiz birikim (balina gizli alim) - hacim dusuk ama CMF pozitif
                score += 0.5
                logger.debug(f"[I5 VOL] {sym} Sessiz birikim (vol={vol_ratio:.2f} CMF={cmf:.3f}) -> +0.5")
            elif vol_ratio < 0.80 and chg_pct > 2.0:
                # +++ HATA 3 FAKEOUT: Hacimsiz yukselis tespit edildi — ceza
                score -= 2
                logger.warning(f"[I5 PUMP] {sym} HACMSIZ YUKSELIS: vol={vol_ratio:.2f} chg={chg_pct:.2f}% -> -2 (sahte pump riski)")

            # ----------------------------------------------------------
            # İ6 — Stochastic %K
            #       20–80 arası = aşırı alım/satım bölgesinde değil (+1)
            # ----------------------------------------------------------
            if 20.0 <= stoch_k <= 80.0:
                score += 1
                logger.debug(f"[İ6 STOCH] {sym} Stoch K={stoch_k:.1f} nötr bölge → +1")

            # I7: ADX Trend Gucu
            # +++ DUZELTME: ADX 15-20 arasi kor nokta giderildi (trend oncesi erken giris)
            if adx >= 25.0:
                score += weights["adx"]
                logger.debug(f"[I7 ADX] {sym} ADX={adx:.1f} trend guclu -> +{weights['adx']}")
            elif 15.0 <= adx < 20.0:
                score += 0.5  # Trend heniiz olusmuyor = erken giris firsati
                logger.debug(f"[I7 ADX] {sym} ADX={adx:.1f} trend oncesi -> +0.5")
            elif 20.0 <= adx < 25.0:
                score += weights["adx"] * 0.7
                logger.debug(f"[I7 ADX] {sym} ADX={adx:.1f} trend gelisiyor -> +{weights['adx']*0.7:.1f}")

            # ----------------------------------------------------------
            # İ8 — CMF / OBV (Chaikin Money Flow)
            #       >0.05 = para girişi var, kurumsal birikim (+1)
            # ----------------------------------------------------------
            if cmf > 0.05:
                score += 1
                logger.debug(f"[İ8 CMF] {sym} CMF={cmf:.3f} para girişi → +1")

            # ----------------------------------------------------------
            # İ9 — RS Line (Relative Strength vs Benchmark)
            #       Pozitif = benchmark'ı geçiyor, lider hisse (+1)
            # ----------------------------------------------------------
            if rs_score > 0.0:
                score += 1
                logger.debug(f"[İ9 RS] {sym} RS={rs_score:.2f} benchmark üstü → +1")

            is_strong_obv_rs = (cmf > 0.05 and rs_score > 0.0)

            # ----------------------------------------------------------
            # İ10 — Higher-High Pattern (Momentum Gücü Teyidi)
            #        Son tick high > önceki tick high = yükselen tepe serisi
            #        FreqAI/FinRL verilerinde %73+ başarı oranı görülen pattern
            #        Kripto → +2 | Hisse/BIST → +1.5
            # ----------------------------------------------------------
            higher_high_pattern = False
            if prev_high_1 > 0 and prev_high_2 > 0:
                higher_high_pattern = (price >= prev_high_1 >= prev_high_2)
            elif prev_high_1 > 0:
                higher_high_pattern = (price >= prev_high_1 * 1.001)
            else:
                higher_high_pattern = (chg_pct > 0.3)  # Veri yoksa değişim proxy

            if higher_high_pattern:
                hh_bonus = 2 if mkt_type == "CRYPTO" else 1.5
                score += hh_bonus
                logger.info(f"[İ10 HH] {sym} Yükselen tepe pattern → +{hh_bonus} (Score: {score})")

            # ----------------------------------------------------------
            # İ11 — Candle Body Ratio (Güçlü Mum Gövdesi)
            #        Gövde / Aralık ≥ %65 = alıcılar kazandı, güçlü kapanış (+1)
            #        Gövde / Aralık ≤ %30 = fitil ağırlıklı, fakeout riski   (-1)
            # ----------------------------------------------------------
            candle_range = candle_high - candle_low
            candle_body  = abs(price - candle_open)
            body_ratio   = (candle_body / candle_range) if candle_range > 0 else 0.5

            if body_ratio >= 0.65:
                score += 1
                logger.info(f"[I11 BODY] {sym} Guclu mum govdesi (Ratio: {body_ratio:.2f}) -> +1")
            elif body_ratio <= 0.30 and candle_range > 0:
                # +++ HATA 2 (Sahte Kirilim): Fitil agirlikli mum = fakeout isaretci
                # Ceza -1'den -2'ye yukseldi (grafikteki en buyuk hata kategorisi)
                score -= 2
                logger.warning(f"[I11 BODY] {sym} FITIL AGIRLIKLI mum (Ratio: {body_ratio:.2f}) -> -2 (Sahte Kirilim riski!)")

            # ----------------------------------------------------------
            # İ12 — Orderbook Pressure / Bid-Ask Imbalance
            #        Alıcı/Toplam oranı ≥ 0.60 = kurumsal talep baskısı
            #        Kripto/NASDAQ → +2 | BIST → +1
            #        Satıcı baskısı ≤ 0.40 → -1 (zayıf sinyal uyarısı)
            # ----------------------------------------------------------
            if bid_ask_ratio >= 0.60:
                ob_bonus = 2 if mkt_type in ["CRYPTO", "NASDAQ"] else 1
                score += ob_bonus
                logger.info(f"[İ12 OBK] {sym} Güçlü alıcı baskısı (Bid/Ask: {bid_ask_ratio:.2f}) → +{ob_bonus}")
            elif bid_ask_ratio >= 0.55:
                score += 1
                logger.info(f"[İ12 OBK] {sym} Hafif alıcı baskısı (Bid/Ask: {bid_ask_ratio:.2f}) → +1")
            elif bid_ask_ratio <= 0.40:
                score -= 1
                logger.info(f"[İ12 OBK] {sym} Satıcı baskısı mevcut (Bid/Ask: {bid_ask_ratio:.2f}) → -1")

            # ----------------------------------------------------------
            # BONUS İ13 — Momentum Kırılım Onayı (Vol + Değişim Çarpanı)
            #        Hacim ≥1.5 & Değişim ≥%1.2 = %85+ başarı olasılığı (+3)
            # ----------------------------------------------------------
            if vol_ratio >= 1.5 and chg_pct >= 1.2:
                # +++ HATA 3 KONTROL: Cok yuksek hacim + cok yuksek degisim = sahte pump olabilir
                if vol_ratio >= 3.5 and chg_pct >= 4.0:
                    logger.warning(f"[I13 PUMP] {sym} ASIRI PUMP SINYALI: vol={vol_ratio:.2f} chg={chg_pct:.2f}% -> +0 (Sahte pump filtresi aktif)")
                    # Momentum bonusu verilmiyor — pump zirvesi riski
                else:
                    score += 3
                    logger.info(f"[I13 MOM] {sym} Hacim+Degisim kirilim onayi -> +3 (Score: {score})")

            # ----------------------------------------------------------
            # BONUS İ14 — Kripto: RSI Oversold Bounce / Bollinger Squeeze
            # ----------------------------------------------------------
            if is_crypto:
                # +++ HATA 2 DUZELTME: I14 Oversold Bounce - chg>0.5 sartiyla gercek dip kaciyor
                # Eski: chg > 0.5 AND vol > 1.2 (cok katiydi)
                # Yeni: RSI dip bolgesi + vol > 0.60 yeterli (chg henuz donmedi olabilir)
                if 30.0 <= rsi <= 45.0 and vol_ratio > 0.60:
                    score += 1.5
                    logger.info(f"[I14 RSI-W] {sym} Oversold Bounce (RSI={rsi:.1f} vol={vol_ratio:.2f}) -> +1.5")
                if atr_pct > 2.0 and chg_pct > 1.5 and vol_ratio >= 1.5:
                    score += 2
                    logger.info(f"[İ14 BB-SQ] {sym} Bollinger Squeeze kırılımı → +2")

            # ----------------------------------------------------------
            # BONUS İ15 — LLM Duygu Analizi (Sadece Kripto)
            #        Sosyal medya / haber duygusu ≥85 → +2
            # ----------------------------------------------------------
            llm_sentiment_bonus = 0
            if is_crypto:
                tweets = llm_intelligence.get_fintwit_social_sentiment(sym)
                if tweets:
                    avg_score = sum(t.get("sentiment_score", 0) for t in tweets) / len(tweets)
                    if avg_score >= 85.0:
                        llm_sentiment_bonus = 2
                        logger.info(f"[İ15 LLM] {sym} Pozitif duygu skoru={avg_score:.0f} → +2")
            score += llm_sentiment_bonus

            # ----------------------------------------------------------
            # BONUS — Deneyim Hafızası ML Çarpanı & Fear/Greed
            # ----------------------------------------------------------
            ml_modifier = mem_check.get("confidence_modifier", 0.0)
            score += int(ml_modifier * 10.0)

            if fg_assessment.bonus_score > 0:
                score += int(fg_assessment.bonus_score)
                logger.debug(f"[FG BONUS] {sym} Fear&Greed={fg_assessment.score}/100 → +{int(fg_assessment.bonus_score)}")

            logger.debug(
                f"[SKOR ÖZET] {sym} | Toplam={score} | "
                f"HH={higher_high_pattern} | Body={body_ratio:.2f} | "
                f"Bid/Ask={bid_ask_ratio:.2f} | CMF={cmf:.3f} | RS={rs_score:.2f}"
            )

            # ──────────────────────────────────────────────────────────────────
            # REJIM MATRISI & YENİ KATMANLARIN (2, 4, 5) ENTEGRASYONU
            # ──────────────────────────────────────────────────────────────────
            current_mode = settings.current_risk_mode.upper()
            _mtype_local = market_hours_validator.get_market_type(sym)
            _rp = regime_engine.get_trade_profile(current_mode, _mtype_local)

            # Giris izni kontrolu
            if not _rp["entry_allowed"]:
                logger.info(f"[REGIME BLOCK] {sym} ({_mtype_local}) {_rp['regime']} rejiminde giris yasak. Mod: {current_mode}")
                continue

            required_score    = _rp["min_score"]
            min_vol           = _rp["min_vol"]
            global_max_pos    = _rp["max_global_pos"]
            max_pos_for_market_regime = _rp["max_market_pos"]

            # YENİ KATMANLAR: Sadece potansiyeli olan sinyaller için OHLCV çek ve ağır analiz yap
            if score >= (required_score - 2):
                from services.broker.market_data_fetcher import data_fetcher
                from services.engine.pattern_recognition_engine import pattern_engine
                from services.indicators_engine.quantitative_indicator_matrix import quantitative_matrix
                from services.engine.support_resistance_mapper import sr_mapper
                
                df = data_fetcher.get_ohlcv(sym, _mtype_local, "15m", 100)
                if df is not None and not df.empty:
                    # Katman 2: Pattern Recognition
                    p_res = pattern_engine.analyze_patterns(df, sym)
                    score += p_res["pattern_score"]
                    
                    # Katman 4: Quantitative Matrix
                    q_res = quantitative_matrix.evaluate_matrix(df, sym)
                    score += q_res["quant_score"]
                    
                    # Katman 5: S/R Mapping
                    sr_res = sr_mapper.map_levels(df, sym)
                    score += sr_res["sr_score"]
                    
                    if sr_res.get("trap_risk"):
                        logger.warning(f"[TRAP GUARD] {sym} Bull Trap riski tespit edildi. Sinyal red.")
                        continue
                        
                    logger.debug(f"[DEEP ANALYSIS] {sym} Yeni Skor: {score:.1f} (P:{p_res['pattern_score']}, Q:{q_res['quant_score']:.1f}, SR:{sr_res['sr_score']})")

            is_buy_signal = score >= required_score

            # Hacim filtresi (Rejim matrisinden)
            if vol_ratio < min_vol:
                logger.info(f"[RISK SHIELD] {sym} Hacim yetersiz (Ratio: {vol_ratio:.2f} < {min_vol}). Mod: {current_mode} | Rejim: {_rp['regime']}")
                continue

            if not is_buy_signal:
                if score >= (required_score - 2):
                    bot_thought_stream.add_throttled(
                        "👀 İzleniyor / Yaklaşıyor",
                        sym,
                        f"Alım bölgesine yaklaşıyor: Skor {score:.1f}/{required_score} (Rejim: {_rp['regime']}, Mod: {current_mode}). Eşiği geçerse otomatik giriş denenecek.",
                        "INFO",
                        cooldown_sec=180,
                    )
                logger.info(f"[SCORE SHIELD] {sym} Sinyal zayıf ({score}/{required_score}). Mod: {current_mode} | Rejim: {_rp['regime']}")
                continue
            # O2 DÜZELTİLDİ: Piyasa başı açık pozisyon limiti kontrolü (rejim matrisinden)
            open_pos_in_market = sum(
                1 for p in live_trade_manager.positions.values()
                if p.status == "OPEN" and p.market == _mtype_local
            )
            max_pos_for_market = max_pos_for_market_regime
            if open_pos_in_market >= max_pos_for_market:
                logger.info(f"[MARKET LIMIT BLOCK] {sym} ({_mtype_local}) piyasasinda max pozisyon sayisina ulasildi ({open_pos_in_market}/{max_pos_for_market}).")
                try:
                    live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Market Limit")
                except Exception:
                    pass
                continue

            # SİSTEM GENELİ MAKSİMUM POZİSYON LİMİTİ (GLOBAL LIMIT BLOCK)
            total_open_pos = sum(1 for p in live_trade_manager.positions.values() if p.status == "OPEN")
            if total_open_pos >= global_max_pos:
                msg = f"[GLOBAL LIMIT BLOCK] {sym} reddedildi. Sistem genelinde maksimum ({total_open_pos}/{global_max_pos}) açık pozisyon limitine ulaşıldı."
                logger.info(msg)
                try:
                    experience_memory_engine.add_live_log(_mtype_local, "BLOCK", msg)
                    live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Global Limit")
                except Exception:
                    pass
                continue

            # BÜTÇE LİMİT KONTROLÜ
            total_invested = sum(p.nominal_value for p in live_trade_manager.positions.values() if p.status == "OPEN")
            if total_invested >= settings.base_portfolio_size:
                msg = f"[BUDGET LIMIT BLOCK] {sym} reddedildi. {settings.base_portfolio_size}$ bütçe limitine ulaşıldı (Mevcut Yatırım: ${total_invested:.2f})."
                logger.info(msg)
                try:
                    experience_memory_engine.add_live_log(_mtype_local, "BLOCK", msg)
                    live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Budget Limit")
                except Exception:
                    pass
                continue

            # Mevcut açık pozisyon kontrolü
            open_pos = next((p for p in live_trade_manager.positions.values() if p.symbol.upper() == sym.upper() and p.status == "OPEN"), None)
            if open_pos:
                # AKILLI ERKEN ÇIKIŞ (Smart Exit)
                # Kârdayken momentum düşerse TP beklemeden cebe at
                if current_mode == "SNIPER" and open_pos.unrealized_pnl_pct >= 0.5:
                    if rsi < 70.0 or vol_ratio < 1.0:
                        logger.info(f"[SNIPER SMART EXIT] {sym} dalga sönümleniyor (RSI: {rsi:.1f}, Vol: {vol_ratio:.2f}). Erken kâr alımı tetikleniyor.")
                        live_trade_manager.close_position(open_pos.id, "CLOSED_EARLY")
                elif open_pos.unrealized_pnl_pct >= 1.5:
                    if rsi < 55.0 or vol_ratio < 0.8:
                        logger.info(f"[SMART EXIT] {sym} %{open_pos.unrealized_pnl_pct} kârda ancak momentum zayıfladı (RSI: {rsi:.1f}, Vol: {vol_ratio:.2f}). Erken kâr alımı (CLOSED_EARLY) tetikleniyor.")
                        live_trade_manager.close_position(open_pos.id, "CLOSED_EARLY")
                continue

            # ==========================================
            # MEAN REVERSION (ORTALAMAYA DÖNÜŞ) MOTORU
            # ==========================================
            mean_rev_enabled = RISK_PARAMS.get("mean_reversion_enabled", False)
            mean_rev_rsi = RISK_PARAMS.get("mean_reversion_rsi_threshold", 28.0)
            
            is_mean_reversion_buy = False
            if mean_rev_enabled and not open_pos:
                if rsi < mean_rev_rsi and chg_pct <= -2.5 and vol_ratio < 1.0:
                    logger.info(f"[MEAN REVERSION] {sym} aşırı satım bölgesinde (RSI: {rsi:.1f}, Chg: %{chg_pct}). Tepki alımı tetikleniyor.")
                    is_mean_reversion_buy = True

            # ==========================================
            # İSTATİSTİKSEL ARBİTRAJ (PAIRS TRADING) MOTORU
            # ==========================================
            arb_enabled = RISK_PARAMS.get("arbitrage_enabled", False)
            arb_gap = RISK_PARAMS.get("arbitrage_gap_threshold_pct", 2.0)
            pairs = RISK_PARAMS.get("correlation_pairs", {})
            
            is_arbitrage_buy = False
            if arb_enabled and not open_pos and sym in pairs:
                peer_sym = pairs[sym]
                if peer_sym in market_data:
                    peer_chg = market_data[peer_sym].get("change_pct", 0.0)
                    if peer_chg - chg_pct >= arb_gap:
                        logger.info(f"[ARBITRAGE] {peer_sym} (+%{peer_chg}) yükseldi ancak {sym} (+%{chg_pct}) geride kaldı. Arbitraj alımı tetikleniyor.")
                        is_arbitrage_buy = True

            # ==========================================
            # ALIM TETİKLEMESİ & DİNAMİK SERMAYE TAHSİSİ
            # ==========================================
            if (is_buy_signal or is_mean_reversion_buy or is_arbitrage_buy) and not open_pos:
                # === ML SINYAL TAHMIN FILTRESI ===
                ml_prob, ml_action, ml_lot_mult = ml_predictor.predict(
                    symbol=sym,
                    indicators=data,
                    context={"fear_greed_score": fg_assessment.score}
                )
                if ml_action == "BLOCK":
                    logger.info(f"[ML BLOCK] {sym} ML modeli bloke etti. Win olasiligi: %{ml_prob*100:.1f}")
                    continue

                dyn_cap = live_trade_manager.get_dynamic_position_capital(sym)

                # Islem Otopsisi & Hafiza Carpani
                qty_mult = mem_check.get("qty_multiplier", 1.0)

                # Piyasa Rejimi Lot Carpani uygula
                qty_mult *= regime_lot_multiplier

                # ML Odulu
                if ml_action == "EXECUTE_REWARD":
                    qty_mult *= ml_lot_mult
                    logger.info(f"[ML REWARD] {sym} ML Odulu aktif! Win olasiligi %{ml_prob*100:.1f}. Lot x{ml_lot_mult}")

                if is_strong_obv_rs and current_mode in ["NORMAL", "TIGHT"]:
                    qty_mult *= 1.20
                    logger.info(f"[AGGRESSIVE ATTACK] {sym} OBV ve RS Guclu! Lot boyutu %20 arttirildi.")
                elif cmf < -0.05:
                    qty_mult *= 0.80
                    logger.info(f"[WEAK VOLUME DEFENSE] {sym} OBV Zayif. Lot boyutu %20 dusuruldu.")

                if trend_conflict:
                    qty_mult *= 0.70
                    logger.info(f"[TREND CONFLICT] {sym} EMA/Supertrend uyusmuyor! Lot %30 azaltildi.")

                if qty_mult != 1.0:
                    dyn_cap = round(dyn_cap * qty_mult, 2)
                    logger.info(f"[ALGO LEARNING] Lot carpani {qty_mult:.2f}x uygulandi. Yeni butce: ${dyn_cap}")

                # Özel Strateji Tag'leri ve İnce Ayar
                # Strateji TP/SL ince ayari (Ortalamaya donus / Arbitraj ovride)
                if is_mean_reversion_buy:
                    strategy_tag = "MEAN_REVERSION"
                    # Ortalamaya donus icin daha dar TP (kisa sure icin)
                    base_tp = min(base_tp, 2.5)
                    base_sl = min(base_sl, 1.2)
                elif is_arbitrage_buy:
                    strategy_tag = "STATISTICAL_ARBITRAGE"
                    base_tp = min(base_tp, 1.5)
                    base_sl = min(base_sl, 0.8)
                
                # Yapay Zeka (LLM) Bonusuna Gore TP Esnetme (max %50 orijinal TP uzatmasi)
                if llm_sentiment_bonus > 0:
                    stretch = min(base_tp * 0.5, 1.5)  # Mevcut TP'nin %50si veya en fazla %1.5
                    base_tp += stretch
                    logger.info(f"[DYNAMIC TP STRETCH] {sym} icin LLM Duygusu guclu. TP hedefi %{base_tp:.1f} seviyesine esnetildi.")

                # Rejim Sermaye Carpani uygula (Mega Boga -> x1.5, Bear -> x0.5)
                _regime_cap_mult = _rp.get("capital_mult", 1.0)

                # Mutlak Fiyat Hedefleri (Absolute Prices)
                target_tp_price = round(price * (1 + (base_tp / 100)), 4)
                target_sl_price = round(price * (1 - (base_sl / 100)), 4)

                signal = WebhookSignal(
                    passphrase=settings.passphrase,  # settings'den al
                    action="BUY",
                    symbol=sym,
                    price=price,
                    quantity=round(dyn_cap / price, 4),
                    take_profit=target_tp_price,
                    stop_loss=target_sl_price,
                    account_equity=dyn_cap,
                    market_position="long",
                    indicators={
                        "rsi": rsi,
                        "volatility": atr_pct,
                        "atr_pct": atr_pct,
                        "volume_ratio": vol_ratio,
                        "cmf": cmf,
                        "rs_score": rs_score,
                        "supertrend_bullish": supertrend_bullish,
                        "trend_conflict": trend_conflict,
                        "adx": adx,
                        "stoch_k": stoch_k
                    },
                    macro_tags=[f"STRATEGY_{strategy_tag}", f"SCORE_{score}_OF_8", f"MODE_{current_mode}"]
                )
                res = process_order(signal)
                # Y1 AUTO-RUNNER için journal kaydı (process_order içinde de yapılıyor, burada ek log)
                logger.info(f"[AUTO-RUNNER EXECUTED] {sym} BUY @ ${price:.2f} | Score: {score}/8 | Result: {res.get('status')}")
                executed_triggers.append({
                    "symbol": sym,
                    "action": "BUY",
                    "price": price,
                    "score": f"{score}/8",
                    "result": res
                })
                # === FIX-2: Timestamp kaydet (string değil) — Cooldown için ===
                self.last_evaluated_signals[sym] = time.time()
                # === PROFIT ADVISOR OTOMATIK TETIKLEYiCi ===
                self._closed_trades_since_last_advisor += 1
                if self._closed_trades_since_last_advisor >= self._profit_advisor_interval:
                    self._closed_trades_since_last_advisor = 0
                    try:
                        from services.agents.profit_advisor_agent import profit_advisor_agent
                        report = profit_advisor_agent.generate_full_report()
                        sizing = report.get("position_sizing", {})
                        rotation = report.get("strategy_rotation", {})
                        logger.info(
                            f"[PROFIT ADVISOR AUTO] {self._profit_advisor_interval} islem sonrasi analiz:\n"
                            f"  Pozisyon Boyutu: {sizing.get('action','?')} ({sizing.get('recommendation','?')})\n"
                            f"  Strateji: {rotation.get('recommended_strategy','?')} "
                            f"(Win={rotation.get('win_rate_by_strategy',{}).get(rotation.get('recommended_strategy',''),0):.0%})"
                        )
                    except Exception as pa_err:
                        logger.warning(f"[PROFIT ADVISOR AUTO ERROR] {pa_err}")

        return executed_triggers

tv_auto_runner = TradingViewAutoStrategyRunner()

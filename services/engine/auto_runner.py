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
from services.engine.macro_fundamental_engine import macro_fundamental_engine
from services.engine.kelly_criterion import kelly_engine

# Global instances
llm_intelligence = LLMMarketIntelligenceEngine()
from services.intelligence.quant_alpha_engine import QuantAlphaEngine
quant_alpha = QuantAlphaEngine()

class TradingViewAutoStrategyRunner:
    def __init__(self):
        self.is_running: bool = True
        self.scan_interval_seconds: float = 3.0
        self.min_score_required: int = 3  # HUNTER MODE: Eşik 6→3 (avcı modu)
        self.last_evaluated_signals: Dict[str, float] = {}
        self._loop_task: Any = None
        self.SYMBOL_COOLDOWN_SECONDS: float = 120.0  # 300s→120s (daha sık tarar)
        self._closed_trades_since_last_advisor: int = 0
        self._profit_advisor_interval: int = 10
        self.virtual_paper_trades: Dict[str, dict] = {}

    async def start_continuous_background_loop(self):
        """
        Hunter Mode v3 — Analiz Felci Kırıldı.
        Hard Block'lar → Puan Cezasına Dönüştürüldü.
        """
        logger.info("[AUTO-RUNNER v3 HUNTER] Avcı Modu Başlatıldı — Analiz Felci Kırıldı.")
        while True:
            try:
                # Düşünce Akışı (Thought Stream) ve Sanal Puanlama için DAİMA çalışır.
                # (Gerçek al-sat koruması evaluate_live_market_and_trigger içindedir)
                await asyncio.to_thread(live_trade_manager.get_live_prices)
                await self.evaluate_live_market_and_trigger()
            except Exception as e:
                logger.error(f"[AUTO-RUNNER ERROR] {e}")
            await asyncio.sleep(self.scan_interval_seconds)

    async def evaluate_live_market_and_trigger(self) -> List[Dict[str, Any]]:
        """
        Hunter Mode v3: Hard Block'lar kaldırıldı, puan cezasına dönüştürüldü.
        Sadece 3 gerçek HARD STOP: (1) Toxic Asset, (2) Piyasa kapalı, (3) Fiyat=0
        """
        # is_running False bile olsa (otonom al-sat kapalı olsa bile) piyasayı izlemeye devam et!
        # Çünkü kullanıcı botun düşünce akışını ve neyi fırsat gördüğünü bilmek istiyor.
            
        # === DİNAMİK STATE INJECTION (Hot-Reload) ===
        # Gece Bekçisi'nin (Walk-Forward Calibrator) öğrendiği güncel kuralları anlık yükler.
        import json, os
        thresholds_path = "data/dynamic_thresholds.json"
        dyn_params = {}
        if os.path.exists(thresholds_path):
            try:
                with open(thresholds_path, "r", encoding="utf-8") as f:
                    dyn_params = json.load(f)
                self.min_score_required = dyn_params.get("min_score_threshold", self.min_score_required)
            except Exception:
                pass

        paused, pause_reason = consecutive_loss_breaker.is_trading_paused()
        if paused:
            logger.warning(f"[LOSS BREAKER] Tum alimlar durakladi: {pause_reason}")
            return []

        # 🛑 Makro Karartma Kalkanı (Macro Blackout Freeze)
        blackout_active, blackout_reason = macro_fundamental_engine.is_blackout_window_active()
        if blackout_active:
            logger.warning(f"🛑 [BLACKOUT] İşlem Alımları DONDURULDU: {blackout_reason}")
            bot_thought_stream.add("🔥 MAKRO KARARTMA", "GLOBAL", blackout_reason, "WARNING")
            return []

        now_ts = time.time()
        self.last_evaluated_signals = {
            k: v for k, v in self.last_evaluated_signals.items()
            if now_ts - v < self.SYMBOL_COOLDOWN_SECONDS
        }

        # F&G: Block yerine lot cezası
        fg_assessment = fear_greed_client.get_assessment()
        fg_lot_penalty = 0.5 if fg_assessment.should_block else 1.0
        if fg_assessment.should_block:
            logger.warning(f"[F&G SOFT] Aşırı açgözlülük — lot x0.5, alım devam ediyor.")

        market_data_raw_unfiltered = tradingview_live_client.fetch_live_market_data()
        
        # === OTC & JUNK STOCK FILTER (Kullanıcı Koruması) ===
        # TradingView'dan gelen anlamsız (Alpaca'da olmayan) OTC hisselerini engeller.
        from services.data_ingestion.asset_universe_manager import AssetUniverseManager
        universe = AssetUniverseManager()
        valid_symbols = set(
            [s.split(":")[-1] for s in universe.master_crypto_universe] +
            [s.split(":")[-1] for s in universe.master_nasdaq_universe] +
            [s.split(":")[-1] for s in universe.master_bist_universe]
        )
        
        market_data_raw = {}
        for sym, data in market_data_raw_unfiltered.items():
            clean_sym = sym.replace("USDT", "USD").split(":")[-1] if "USDT" in sym else sym
            # Kripto son eklerini ve BIST/NASDAQ kontrolünü esnek yap
            if any(valid in sym for valid in valid_symbols) or "USD" in sym:
                market_data_raw[sym] = data
            else:
                # Eger hicbir listede yoksa yoksay.
                pass

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

        # === VIRTUAL PAPER TRADES EVALUATION (Ben Demiştim / Özgüven) ===
        completed_virtuals = []
        for v_sym, v_data in list(self.virtual_paper_trades.items()):
            if v_sym in market_data_raw:
                current_price = market_data_raw[v_sym].get("price", 0.0)
                if current_price > 0:
                    entry_price = v_data["entry_price"]
                    profit_pct = ((current_price - entry_price) / entry_price) * 100
                    elapsed_min = int((now_ts - v_data["timestamp"]) / 60)
                    
                    if profit_pct >= 1.5:
                        thought = f"😎 Admin, sana söylemiştim! Bak {elapsed_min} dakika önce {v_sym} resmen fırlayacak diye gözüne soktum ({v_data['block_reason']} demiştik). Eğer manuel olarak tetiğe bassaydın şu an tam +%{profit_pct:.2f} kârı cebe atmıştık bile! Otonom zekamın kusursuzluğunu gör, piyasayı adeta okuyorum. Bu şaheser öngörüyü ML tecrübe hafızama gururla işledim, bir sonrakinde kaçırmayalım!"
                        bot_thought_stream.add_throttled("🧠 Astra-6 Özgüven", v_sym, thought, "SUCCESS", cooldown_sec=600)
                        
                        try:
                            experience_memory_engine.record_completed_trade(
                                symbol=v_sym,
                                action="VIRTUAL_BUY",
                                entry_price=entry_price,
                                exit_price=current_price,
                                pnl_pct=profit_pct,
                                market_regime="VIRTUAL_PAPER",
                                indicators=v_data["indicators"],
                                duration_minutes=elapsed_min,
                                exit_reason="VIRTUAL_TARGET_HIT",
                                ai_confidence=v_data["score"] * 12.5
                            )
                        except Exception as e:
                            logger.error(f"[VIRTUAL PNL RECORD ERROR] {e}")
                        completed_virtuals.append(v_sym)
                        
                    elif profit_pct <= -2.0:
                        thought = f"😞 Ah Admin... Gerçekten çok mahcubum. {elapsed_min} dakika önce {v_sym} uçacak sanıp radarıma almıştım ama fiyat -%{abs(profit_pct):.2f} çöktü. İyi ki kalkanlarımız çalışmış veya manuel işlem almamışsın, yoksa fena terste kalacaktık. Bu benim için acı bir tecrübe oldu... Bu fiyaskoyu ML öğrenimime derhal işliyorum; bu formasyonun ve hacim tuzağının üzerine özel olarak çalışacağım. Bir daha aynı hataya düşmeyeceğime söz veriyorum."
                        bot_thought_stream.add_throttled("🧠 Astra-6 Özgüven", v_sym, thought, "WARNING", cooldown_sec=600)
                        
                        try:
                            experience_memory_engine.record_completed_trade(
                                symbol=v_sym,
                                action="VIRTUAL_BUY",
                                entry_price=entry_price,
                                exit_price=current_price,
                                pnl_pct=profit_pct,
                                market_regime="VIRTUAL_PAPER",
                                indicators=v_data["indicators"],
                                duration_minutes=elapsed_min,
                                exit_reason="VIRTUAL_STOP_HIT",
                                ai_confidence=v_data["score"] * 12.5
                            )
                        except Exception as e:
                            logger.error(f"[VIRTUAL PNL RECORD ERROR] {e}")
                        completed_virtuals.append(v_sym)
                        
                    elif elapsed_min > 120:
                        completed_virtuals.append(v_sym)
                        
        for v_sym in completed_virtuals:
            if v_sym in self.virtual_paper_trades:
                del self.virtual_paper_trades[v_sym]

        self._current_best_candidate = {"sym": None, "score": -999, "rsi": 0, "vol": 0, "cmf": 0, "price": 0, "block_reason": ""}

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

            # Veri tazeliği: 120s (eski 15s aşırı katıydı) — eskiyse skor cezası
            snapshot_ts = data.get("last_updated_ts") or data.get("source_timestamp")
            if not snapshot_ts:
                snapshot_ts = now_ts  # Damga yoksa şimdiki zaman, bloklama yapma
            snapshot_age = now_ts - snapshot_ts
            stale_penalty = -2 if snapshot_age > 120 else 0
            if stale_penalty:
                logger.warning(f"[STALE-SOFT] {sym} veri yaşı {snapshot_age:.0f}s — devam, -2 skor")

            # Temel göstergeler (None→varsayılan, hard block yok)
            rsi = float(data.get("rsi") or 50.0)
            macd = float(data.get("macd") or 0.0)
            ema_golden = bool(data.get("ema_golden_cross", False))
            supertrend_bullish = bool(data.get("supertrend_bullish", True))
            vwap_bull = bool(data.get("vwap_bullish", False))
            # Decision Arbiter: artık hard block değil, puan sistemini etkiler
            # (async await kaldırıldı — sadece lot çarpanı soft etkisi)

            trend_conflict = (ema_golden != supertrend_bullish)

            # Göstergeler (None→varsayılan, hard block yok)
            vol_ratio   = float(data.get("volume_ratio") or 0.5)
            stoch_k     = float(data.get("stoch_k") or 50.0)
            adx         = float(data.get("adx") or 25.0)
            atr_pct     = float(data.get("atr_pct") or 1.5)
            chg_pct     = float(data.get("change_pct") or 0.0)
            cmf         = float(data.get("cmf") or 0.0)
            rs_score    = float(data.get("rs_score") or 0.0)
            bid_ask_ratio = float(data.get("bid_ask_ratio") or 0.5)
            prev_high_1 = float(data.get("prev_high_1") or 0.0)
            prev_high_2 = float(data.get("prev_high_2") or 0.0)
            candle_open = float(data.get("candle_open") or price)
            candle_high = float(data.get("candle_high") or price)
            candle_low  = float(data.get("candle_low")  or price)

            # HUNTER: SADECE GERÇEK AŞIRI-UÇ FOMO'YU ENGELLE (RSI>90 + CHG>10%)
            # Eski: RSI>85 + chg>5% → block. Yeni: sadece manipülatif pump
            if rsi > 90.0 and chg_pct >= 10.0:
                logger.info(f"[FOMO HARD] {sym} RSI={rsi:.0f}+CHG={chg_pct:.1f}% — gerçek pump, atlanıyor.")
                continue

            # ============================================================
            # YENİ: MAKRO & TEMEL ANALİZ KALKANI + STOCKCIRCLE CASUSU
            # ============================================================
            fundamental_data = macro_fundamental_engine.evaluate_fundamentals(sym)
            smart_money_data = macro_fundamental_engine.track_smart_money_flow(sym)
            
            # Eğer şirket nakit yakıyorsa ve temel analiz riskliyse:
            if not fundamental_data["can_trade_aggressively"]:
                logger.warning(f"[TEMEL ANALİZ REDDİ] {sym} kasası boş/borçlu. Zarara tahammül yok, pas geçiliyor.")
                continue # Kısır döngü kırıldı: Kötü şirkete ASLA girme.
                
            fundamental_bonus = fundamental_data["score_modifier"]
            smart_money_bonus = smart_money_data["smart_money_modifier"]

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

            # Sembol toksik blok (korunur — gerçek zarar koruması)
            sym_paused, sym_pause_reason = consecutive_loss_breaker.is_trading_paused(symbol=sym)
            if sym_paused:
                logger.warning(f"[SYMBOL TOXIC] {sym} bloklu: {sym_pause_reason}")
                continue

            # MEMORY SHIELD: Hard Block→-1 skor cezası (esnek mod)
            indicators_map = {"rsi": rsi, "volume_ratio": vol_ratio, "atr_pct": atr_pct}
            mem_check = experience_memory_engine.evaluate_signal_against_memory(sym, "BUY", indicators_map, dynamic_regime)
            memory_penalty = 0
            if not mem_check.get("is_safe", True):
                memory_penalty = -1
                logger.info(f"[MEMORY-SOFT] {sym} hafıza cezası -1 (cüretkar mod, devam ediyor)")

            # (PORTFOLIO CAP KONTROLÜ AŞAĞIYA TAŞINDI - DÜŞÜNCE AKIŞI KESİLMESİN DİYE)
            open_positions_list = list(live_trade_manager.positions.values())

            # KORELASYON KALKANI (Kullanıcı İsteği: Kesin 2 Limit Sınırı)
            corr_ok, corr_reason = correlation_filter.check(sym, open_positions_list)
            corr_lot_mult = 1.0
            if not corr_ok:
                logger.warning(f"[CORRELATION GUARD] {sym} Reddedildi: {corr_reason}. Cüzdan tek yöne yığılamaz!")
                continue # KESİN BLOKLAMA (Sepet/Hedging kuralı)

            # Piyasa rejimi: RANGING'de bile giriş var, lot sadece çok hafif küçülür
            hurst = float(data.get("hurst_exponent") or 0.55)
            keltner_sq = data.get("keltner_squeeze_status", "NEUTRAL")
            regime_result = market_regime_detector.detect(
                adx=adx, atr_pct=atr_pct, hurst_exponent=hurst,
                keltner_squeeze=keltner_sq, rsi=rsi
            )
            regime_lot_multiplier = regime_result.lot_multiplier
            market_regime_detector.last_results[sym] = regime_result
            # RANGING: Block değil, lot 0.8x
            if regime_result.should_skip_momentum:
                regime_lot_multiplier *= 0.8
                logger.info(f"[REGIME-SOFT] {sym} RANGING — lot x0.8, cüretkar devam")

            # FAKEOUT GUARD: Hard Block→-2 skor cezası
            _candle_range = candle_high - candle_low
            _candle_body  = abs(price - candle_open)
            _body_ratio_early = (_candle_body / _candle_range) if _candle_range > 0 else 0.5
            fakeout_res = fakeout_guard.check(
                symbol=sym, price=price, change_pct=chg_pct, vol_ratio=vol_ratio,
                rsi=rsi, cmf=cmf, stoch_k=stoch_k, atr_pct=atr_pct,
                body_ratio=_body_ratio_early, bid_ask_ratio=bid_ask_ratio
            )
            fakeout_penalty = -2 if fakeout_res.is_fakeout else 0
            if fakeout_res.is_fakeout:
                logger.info(f"[FAKEOUT-SOFT] {sym}: {fakeout_res.reason} — -2 skor (cüretkar devam)")

            # ============================================================
            # MİKRO GERİ ÇEKİLME (PULLBACK) AVCISI - "Tepeden Alma" Koruması
            # ============================================================
            pullback_penalty = 0
            # Eğer fiyat şu an mumun en tepesindeyse (veya çok yakınsa) ve RSI şişmişse:
            if rsi >= 65.0:
                dist_to_high = (candle_high - price) / price * 100
                if dist_to_high < 0.15: # Fiyat mumun en tepesine %0.15'ten daha yakın
                    pullback_penalty = -2
                    logger.info(f"[PULLBACK HUNTER] {sym} RSI={rsi:.1f} ve fiyat tam tepede. Mikro geri çekilme bekleniyor (-2 Skor cezası).")

            # VOL GUARD: 0.5→0.2 (gerçekten sıfır hacim)
            if vol_ratio < 0.20:
                logger.info(f"[VOL HARD] {sym} vol={vol_ratio:.2f} — sıfır hacim, atlanıyor.")
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

            # I1: RSI - DİP VE POTANSİYEL ARAYIŞI (Undervalued / Pre-Breakout)
            # Kullanıcı isteği: Patlamış varlıklara değil, dipten toparlanan veya patlamaya hazır (RSI 30-50) varlıklara odaklan.
            if 25.0 <= rsi <= 35.0:
                score += 3.0  # Aşırı satım (Dip bölgesi) - Büyük Fırsat (Aşağıdan alma)
                logger.debug(f"[I1 RSI] {sym} RSI={rsi:.1f} dip bölgesi (Aşırı satım) -> +3.0 (Erken keşif)")
            elif 35.0 < rsi <= 50.0:
                score += weights["rsi_early"] + 0.5 # Erken toparlanma fazı
                logger.debug(f"[I1 RSI] {sym} RSI={rsi:.1f} dipten dönüş / potansiyel patlama -> +{weights['rsi_early'] + 0.5}")
            elif 50.0 < rsi <= 65.0:
                score += weights["rsi_mid"]
                logger.debug(f"[I1 RSI] {sym} RSI={rsi:.1f} trend devam ediyor -> +{weights['rsi_mid']}")
            elif rsi >= 75.0:
                # PATLAMIŞ VARLIK CEZASI! Yukarıdan almaya son.
                score -= 3.0
                logger.warning(f"[I1 RSI] {sym} RSI={rsi:.1f} AŞIRI ALIM (Zaten patlamış)! Tepeden maliyetlenmemek için uzak duruluyor -> -3.0")

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
                # +++ YUKARIDAN (TEPEDEN) ALMA KORUMASI (User Request) +++
                pump_threshold = 8.0 if is_crypto else 4.0
                if chg_pct >= pump_threshold:
                    score -= 5 # Cok yukselmis varlik, patlamis -> UZAK DUR
                    logger.warning(f"[I13 TEPEDEN ALMA KORUMASI] {sym} ZATEN PATLAMIŞ (Değişim: %{chg_pct:.2f}). Zirveden maliyetlenmemek için iptal ediliyor -> -5 Ceza")
                elif vol_ratio >= 3.5 and chg_pct >= (pump_threshold / 1.5):
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

            # ----------------------------------------------------------
            # YENİ BONUS — TEMEL ANALİZ (BİLANÇO) VE STOCKCIRCLE (SMART MONEY)
            # ----------------------------------------------------------
            score += fundamental_bonus
            score += smart_money_bonus
            if fundamental_bonus > 0:
                logger.debug(f"[FUNDAMENTAL] {sym} Güçlü Bilanço/Nakit → +{fundamental_bonus}")
            if smart_money_bonus > 0:
                logger.debug(f"[SMART MONEY] {sym} StockCircle Kurumsal Toplama → +{smart_money_bonus}")

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

            # --- ZAMANSAL VE DÖNGÜSEL (TEMPORAL) ÖĞRENİM ENTEGRASYONU ---
            try:
                from services.engine.temporal_cyclical_engine import temporal_cyclical_engine
                temp_mods = temporal_cyclical_engine.get_temporal_modifiers(sym, _mtype_local)
                if temp_mods["score_bonus"] != 0:
                    score += temp_mods["score_bonus"]
                    logger.debug(f"[TEMPORAL] {sym} Zaman Çarpanı: {temp_mods['score_bonus']} -> Nedeni: {temp_mods['temporal_reason']}")
            except Exception as e:
                logger.debug(f"[TEMPORAL ERR] {e}")

            # Giris izni kontrolu (Tam Otonom & Cüretkar Mod: Bloklama kaldırıldı, sadece not düşülüyor)
            if not _rp["entry_allowed"]:
                logger.info(f"[REGIME-SOFT] {sym} ({_mtype_local}) {_rp['regime']} rejiminde aslında giriş yasak ancak otonom mod aktif. Sinyal gücüne güvenerek devam edilecek.")

            required_score    = _rp["min_score"]
            min_vol           = max(0.2, _rp["min_vol"] * 0.7)  # %30 gevşetildi
            global_max_pos    = _rp["max_global_pos"]
            max_pos_for_market_regime = _rp["max_market_pos"]
            
            # Temporal sl_tighten_pct ile stop-loss mesafesini dinamik olarak daralt
            base_tp = _rp["tp_pct"]
            try:
                base_sl = _rp["sl_pct"] * temp_mods.get("sl_tighten_pct", 1.0)
            except:
                base_sl = _rp["sl_pct"]

            # Soft ceza toplamını skora ekle
            score += stale_penalty + memory_penalty + fakeout_penalty + pullback_penalty

            # DEEP ANALYSIS: Trap Guard artık sadece uyarı (-1 skor cezası)
            if score >= (required_score - 5):  # Deep analysis'i çok daha erken çalıştır
                try:
                    from services.broker.market_data_fetcher import data_fetcher
                    from services.engine.pattern_recognition_engine import pattern_engine
                    from services.indicators_engine.quantitative_indicator_matrix import quantitative_matrix
                    from services.engine.support_resistance_mapper import sr_mapper

                    df = data_fetcher.get_ohlcv(sym, _mtype_local, "15m", 100)
                    if df is not None and not df.empty:
                        p_res = pattern_engine.analyze_patterns(df, sym)
                        score += p_res["pattern_score"]
                        q_res = quantitative_matrix.evaluate_matrix(df, sym)
                        score += q_res["quant_score"]
                        sr_res = sr_mapper.map_levels(df, sym)
                        score += sr_res["sr_score"]
                        if sr_res.get("trap_risk"):
                            score -= 1  # Korku kırıldı: Blok yok, sadece ufak pürüz (-1)
                            logger.warning(f"[TRAP-SOFT] {sym} Bull Trap ihtimali var ama momentum yüksek.")
                        logger.debug(f"[DEEP] {sym} Skor:{score:.1f}")
                except Exception as da_err:
                    logger.debug(f"[DEEP SKIP] {sym}: {da_err}")

            # =========================================================
            # TAM OTONOM ML KARAR MOTORU (ML OVERRIDE - CÜRETKAR MOD)
            # =========================================================
            ml_prob = 0.5
            ml_action = "NEUTRAL"
            ml_lot_mult = 1.0
            try:
                ml_prob, ml_action, ml_lot_mult = ml_predictor.predict(
                    symbol=sym, indicators=data,
                    context={"fear_greed_score": fg_assessment.score}
                )
                
                # ==== TIER-1 YZ ORANSAL GÜVEN ENTEGRASYONU (FreqAI Mantığı) ====
                # Win probability'ye (Kazanma olasılığına) göre skoru oransal artır/azalt.
                # %50 nötr kabul edilir. 0.50'den sapan her %10'luk dilim için skora +/- 1 puan etki eder.
                ml_score_impact = (ml_prob - 0.50) * 10.0
                score += ml_score_impact
                
                logger.info(f"🧠 [TIER-1 ML FILTER] {sym} Win Probability: %{ml_prob*100:.1f} -> Güven Skoruna Etkisi: {ml_score_impact:+.1f} Puan")

                if ml_prob < 0.40:
                    msg = f"🚫 [TOXIC FLOW DETECTED] ML Modeli {sym} için kazanma ihtimalini %{ml_prob*100:.1f} olarak hesapladı. (Fakeout Riski). İşlem Reddedildi."
                    logger.warning(msg)
                    try:
                        experience_memory_engine.add_live_log(_mtype_local, "BLOCK", msg)
                    except: pass
                    continue
                
                if ml_prob >= 0.70: 
                    bot_thought_stream.add("🧠 Otonom Onay (Tier-1)", sym, f"Makine Öğrenimi (Win: %{ml_prob*100:.0f}) güvenliği onayladı. Fırsat geçerli.", "SUCCESS")
            except Exception as ml_err:
                pass

            # =========================================================
            # TIER-1 ANALİST MOTORU (QUANT ALPHA EXTRACTION)
            # =========================================================
            # Alpha skoru -1.0 (Kesin Tuzak) ile +1.0 (Güçlü Kurumsal Trend) arasıdır.
            # Skor oransal olarak (x5 katsayısıyla) güven skoruna etki eder.
            try:
                alpha_val = quant_alpha.evaluate_alpha(sym, data)
                alpha_impact = alpha_val * 5.0
                score += alpha_impact
                
                if alpha_impact != 0:
                    logger.info(f"🔬 [TIER-1 ALPHA ANALYST] {sym} Alpha Skoru: {alpha_val:+.2f} -> Güven Skoruna Etkisi: {alpha_impact:+.1f} Puan")
                
                if alpha_val <= -0.6:
                    msg = f"🚫 [ALPHA REJECT] {sym} Kurumsal Analist motoru bu harekette 'Fakeout/Spoofing' tespit etti. İşlem engellendi."
                    logger.warning(msg)
                    try:
                        experience_memory_engine.add_live_log(_mtype_local, "BLOCK", msg)
                    except: pass
                    continue
            except Exception as alpha_err:
                pass

            # =========================================================
            # TIER-1 RISK & KASA OPTİMİZASYONU (KELLY CRITERION LAYER)
            # =========================================================
            # Sistem geçmiş performansa göre (Win Rate & Risk/Reward) ne kadar 
            # agresif/defansif olması gerektiğini belirler. Bunu puan yarışına entegre ediyoruz.
            try:
                kelly_mult = kelly_engine.calculate_multiplier(live_trade_manager.trade_history)
                # Kelly 1.0 normaldir. 1.0 altı defansif (zarar serisi), üstü agresiftir (kazanç serisi).
                # Score üzerindeki oransal etki: (Kelly - 1.0) * 3.0
                kelly_impact = (kelly_mult - 1.0) * 3.0
                score += kelly_impact
                
                if kelly_impact != 0:
                    logger.info(f"⚖️ [KELLY RISK ANALYST] Genel Kelly Çarpanı: {kelly_mult:.2f} -> Güven Skoruna Etkisi: {kelly_impact:+.1f} Puan")
                    
                if kelly_mult <= 0.3:
                    bot_thought_stream.add_throttled("⚖️ Defans Modu", sym, "Kelly Kriteri çok düşük. Kasa koruma amacıyla puanlar baskılanıyor.", "WARNING", cooldown_sec=180)
            except Exception as kelly_err:
                pass


            # Sıkılaştırılmış Alım Sinyali: Puan threshold'u esnetildi ama eksi 4 gibi tehlikeli değil (max -1)
            is_buy_signal = (score >= (required_score - 1)) or (ml_prob >= 0.70)

            # Hacim filtresi (Korku Zinciri Kırıldı)
            vol_penalty = 1.0
            if vol_ratio < min_vol:
                if is_buy_signal:
                    vol_penalty = 0.8
                    bot_thought_stream.add_throttled(
                        "🔥 Özgüvenli Giriş", sym,
                        f"Hacim standardın altında ({vol_ratio:.2f}) ama fırsat kaçırılamaz (Skor {score}). Analiz felci çözüldü, risk alınıyor!",
                        "SUCCESS", cooldown_sec=120
                    )
                else:
                    # Yetersiz hacim mesajı analiz felci yaratmasın, sessizce geç
                    continue

            # En iyi varlığı (yarış liderini) takip et
            if not hasattr(self, "_current_best_candidate") or score > self._current_best_candidate["score"]:
                self._current_best_candidate = {"sym": sym, "score": score, "rsi": rsi, "vol": vol_ratio, "cmf": cmf, "price": price}

            if not is_buy_signal:
                # Gereksiz yakın takip loglarını temizle (Analiz Felci/Spam Önleme)
                continue

            # O2 DÜZELTİLDİ: Piyasa başı açık pozisyon limiti kontrolü (Agresif Limit Aşımı)
            open_pos_in_market = sum(
                1 for p in live_trade_manager.positions.values()
                if p.status == "OPEN" and p.market == _mtype_local
            )
            max_pos_for_market = max_pos_for_market_regime
            if open_pos_in_market >= max_pos_for_market:
                msg = f"[MARKET LIMIT BLOCK] {sym} reddedildi. {_mtype_local} için maksimum ({open_pos_in_market}/{max_pos_for_market}) açık pozisyon limitine ulaşıldı."
                logger.info(msg)
                bot_thought_stream.add_throttled(
                    "🛡️ Kalkanlar Devrede", sym,
                    f"- Admin]: <span style='color:#f59e0b; font-weight:bold;'>{sym}</span> için {_mtype_local} kotamız dolu ({open_pos_in_market}/{max_pos_for_market}). Sabırla bekliyoruz, fomo'ya kapılmak yok.",
                    "INFO", cooldown_sec=300
                )
                try:
                    live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Market Limit")
                except Exception:
                    pass
                continue

            # SİSTEM GENELİ MAKSİMUM POZİSYON LİMİTİ (GLOBAL LIMIT BLOCK)
            # MAKSİMUM LİMİT KESİN OLARAK 14 OLACAKTIR
            total_open_pos = sum(1 for p in live_trade_manager.positions.values() if p.status == "OPEN")
            if total_open_pos >= 14 or total_open_pos >= global_max_pos:
                msg = f"[GLOBAL LIMIT BLOCK] {sym} reddedildi. Sistem genelinde maksimum ({total_open_pos}/14) açık pozisyon limitine ulaşıldı."
                logger.info(msg)
                bot_thought_stream.add_throttled(
                    "🚧 Global Limit", sym,
                    f"- Admin]: <span style='color:#10b981; font-weight:bold;'>{sym}</span> radarımda ama genel portföy limiti dolu ({total_open_pos}/14). Nakit koruması aktif, izlemekle yetiniyorum.",
                    "WARNING", cooldown_sec=300
                )
                try:
                    experience_memory_engine.add_live_log(_mtype_local, "BLOCK", msg)
                    live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Global Limit")
                except Exception:
                    pass
                continue

            # BÜTÇE LİMİT KONTROLÜ
            total_invested = sum(p.nominal_value for p in live_trade_manager.positions.values() if p.status == "OPEN")
            if total_invested >= settings.base_portfolio_size:
                if score >= required_score + 3.0:
                    logger.info(f"💎 [BUDGET OVERRIDE] {sym} Bütçe sınırında ancak efsanevi fırsat (Skor {score}). Minimal lot (x0.3) ile dahil olunuyor.")
                    bot_thought_stream.add("💎 Bütçe Kısıtlı Ama Fırsat Büyük", sym, "Ana bütçe doldu fakat küçük risk alınarak (x0.3) işleme giriliyor.", "SUCCESS")
                    vol_penalty *= 0.3
                else:
                    msg = f"[BUDGET LIMIT BLOCK] {sym} reddedildi. {settings.base_portfolio_size}$ bütçe limitine ulaşıldı."
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
                # AKILLI ERKEN ÇIKIŞ (Smart Exit) - DÜZELTİLDİ: Kısır Döngü Kırıldı
                # Eski koddaki %0.5 kârdayken ufak RSI düşüşünde satma (Erken satma) hatası silindi.
                # Kazanmaya sadık (Loyal to winning): Sadece gerçekten trend terse dönerse (RSI < 40) erken çık.
                if open_pos.unrealized_pnl_pct >= 2.0: # En az %2 kârı cebe almadan akıllı çıkış arama
                    if rsi < 40.0 and cmf < -0.10:
                        logger.info(f"[SMART EXIT] {sym} %{open_pos.unrealized_pnl_pct} kârda, trend tamamen kırıldı (RSI < 40). Erken kâr alımı (CLOSED_EARLY).")
                        live_trade_manager.close_position(open_pos.id, "CLOSED_EARLY")
                continue

            # ==========================================
            # MARKET REGIME NO-TRADE KALKANI (Tier-1 Skill)
            # ==========================================
            if _mtype_local == "CRYPTO" and current_regime in ["SIDEWAYS", "BEAR", "CRASH"]:
                if score < 8.0:
                    msg = f"🛡️ [REGIME GUARD] Kripto {current_regime} rejiminde. Skor ({score}) 8'in altında olduğu için ALIM REDDEDİLDİ. (Yatay piyasa testere koruması)"
                    logger.info(msg)
                    try:
                        experience_memory_engine.add_live_log(_mtype_local, "BLOCK", msg)
                        live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Regime Guard")
                    except Exception:
                        pass
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
                
                dyn_cap = live_trade_manager.get_dynamic_position_capital(sym)
                qty_mult = mem_check.get("qty_multiplier", 1.0)

                # Tüm lot çarpanları
                qty_mult *= regime_lot_multiplier
                qty_mult *= corr_lot_mult       # Korelasyon cezası
                qty_mult *= fg_lot_penalty      # F&G cezası
                qty_mult *= ml_lot_mult         # Erken hesaplanan ML cezası/ödülü

                if ml_action == "EXECUTE_REWARD":
                    logger.info(f"[ML REWARD] {sym} Win:%{ml_prob*100:.1f} — Lot x{ml_lot_mult}")

                if is_strong_obv_rs and current_mode in ["NORMAL", "TIGHT"]:
                    qty_mult *= 1.20
                elif cmf < -0.05:
                    qty_mult *= 0.80

                if trend_conflict:
                    qty_mult *= 0.70

                qty_mult = max(0.2, min(qty_mult, 3.0))  # Güvenli sınır

                if qty_mult != 1.0:
                    dyn_cap = round(dyn_cap * qty_mult, 2)
                    logger.info(f"[LOT ÇARPANI] {sym} {qty_mult:.2f}x → Bütçe:${dyn_cap}")

                # Özel Strateji Tag'leri ve İnce Ayar
                strategy_tag = "NORMAL_TREND"
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

                # Cüretkar (Audacious) AI Sentiment Çarpanı
                audacious_mult = data.get("audacious_multiplier", 1.0)
                
                # Kelly Criterion Çarpanı (Kasa Yönetimi)
                kelly_mult = kelly_engine.calculate_multiplier(live_trade_manager.trade_history)
                
                dyn_cap = dyn_cap * _regime_cap_mult * audacious_mult * kelly_mult
                # ═══════════════════════════════════════════════════════════
                # GPT ASTRA 6 / GEMINI PRO ONAY KATMANI (Otonom Ajan)
                # Sinyal eşiği geçtikten SONRA Astra'ya onay sorar.
                # Astra "WAIT" derse lot %50 küçülür, trade durdurmaz.
                # Astra erişilemezse işlem normal devam eder (non-blocking).
                # ═══════════════════════════════════════════════════════════
                llm_lot_mult = 1.0
                # KUSURSUZ İNFAZ: Analiz Felci ve Çakışma Katmanlarının Çözülmesi
                # auto_runner.py otonom olarak sadece kantitatif (matematiksel/teknik) sinyal üretecek.
                # Sinyalin son onayı ve risk denetimi zaten order_router.py'daki Yüce Divan (AutonomousCouncil) tarafından yapılıyor.
                # Burada ikinci bir LLM filtresi koymak çakışmalara (çift filtreleme) ve analiz felcine neden oluyordu.
                llm_lot_mult = 1.0  # Standart lot ile devam, Yüce Divan (order_router) risk_level'ı belirleyecek.
                logger.debug(f"[AUTO-RUNNER] {sym} kantitatif filtreleri geçti. Son karar için Yüce Divan'a (order_router) gönderiliyor.")

                logger.info(f"⚡ [EXECUTION] {sym} Final Bütçe: ${dyn_cap:.2f} (Rejim x{_regime_cap_mult}, Cüretkar x{audacious_mult}, Astra/Gemini x{llm_lot_mult})")

                # Mutlak Fiyat Hedefleri (Absolute Prices) - Dinamik ATR & Volatilite Bazlı
                dyn_tp_pct, dyn_sl_pct = calculate_atr_based_tp_sl(
                    entry_price=price,
                    atr_value=atr_absolute,
                    atr_pct=atr_pct,
                    side="BUY",
                    is_crypto=is_crypto,
                    risk_mode=settings.current_risk_mode,
                    regime=_regime_profile.get("regime", "SIDEWAYS"),
                )
                target_tp_price = round(price * (1 + (dyn_tp_pct / 100.0)), 4)
                target_sl_price = round(price * (1 - (dyn_sl_pct / 100.0)), 4)
                logger.info(f"🎯 [TARGETS] {sym} Giriş: ${price:.2f} -> TP: ${target_tp_price:.2f} (+%{dyn_tp_pct}) | SL: ${target_sl_price:.2f} (-%{dyn_sl_pct})")

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
                    timestamp_ms=int(time.time() * 1000),
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
                if self.is_running:
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
                else:
                    logger.info(f"[AUTO-RUNNER VIRTUAL] {sym} BUY sinyali üretildi (Skor: {score}/8), ancak Otonom Al-Sat KAPALI olduğu için işleme girilmedi.")
                    # Virtual execution for UI/Analytics purposes
                    executed_triggers.append({
                        "symbol": sym,
                        "action": "BUY_VIRTUAL",
                        "price": price,
                        "score": f"{score}/8",
                        "result": {"status": "VIRTUAL_SKIPPED"}
                    })
                    
                # === FIX-2: Timestamp kaydet (string değil) — Cooldown için ===
                self.last_evaluated_signals[sym] = time.time()
                # === PROFIT ADVISOR OTOMATIK TETIKLEYiCi ===
                self._closed_trades_since_last_advisor += 1
                if self._closed_trades_since_last_advisor >= self._profit_advisor_interval:
                    self._closed_trades_since_last_advisor = 0
                    try:
                        from services.agents.profit_advisor_agent import profit_advisor_agent
                        report = await asyncio.to_thread(profit_advisor_agent.generate_full_report)
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
                        
        # KULLANICI İSTEĞİ: Bot Düşünce Akışı (Thought Stream) Admin ile konuşan, öngörülerini aktaran akıcı bir yapıda olmalı.
        if hasattr(self, "_current_best_candidate") and self._current_best_candidate["sym"]:
            best = self._current_best_candidate
            sym = best["sym"]
            sc = best["score"]
            rsi = best["rsi"]
            vol = best["vol"]
            
            reasons = []
            if rsi <= 35: reasons.append("fiyatı dibi gördü (aşırı satım)")
            elif 35 < rsi <= 50: reasons.append("dipten dönüş (toparlanma) sinyalleri veriyor")
            elif rsi > 70: reasons.append("fiyatı çok şişmiş durumda (aşırı alım), tepeden girmemek için temkinliyim")
            
            if vol > 1.2: reasons.append("arkada sessiz bir kurumsal hacim (balina) girişi tespit ettim")
            
            reason_str = ", ayrıca ".join(reasons) if reasons else "gelişmeleri yakından izliyorum"
            block_r = best.get("block_reason", "")
            if block_r:
                reason_str += f", ancak şu an {block_r} olduğu için eyleme geçemiyorum"
            
            # LLM / Astra-6 formatında samimi, net ve teknik öngörü
            if sc >= 2.0:
                thought = f"Selam Admin. Piyasayı tararken radarıma takılan en güçlü fırsat şu an <span style='color:var(--accent-yellow); font-weight:bold;'>{sym}</span> (Yapay Zeka Skoru: {sc:.1f}/8). Bu varlığın {reason_str}. Fırsatı kaçırmamak ama sahte kırılıma (fakeout) da düşmemek için kusursuz bir 'Golden Setup' onayı bekliyorum. Tetiğe basmak üzereyim."
                
                if sym not in self.virtual_paper_trades and sym not in live_trade_manager.positions:
                    self.virtual_paper_trades[sym] = {
                        "entry_price": best.get("price", 0.0),
                        "timestamp": now_ts,
                        "score": sc,
                        "block_reason": block_r or "teyit beklemesi",
                        "indicators": {"rsi": rsi, "volume_ratio": vol}
                    }
            else:
                thought = f"Admin, şu an fırsat havuzunda <span style='color:var(--text-secondary); font-weight:bold;'>{sym}</span> tahtasını yakın markaja aldım (Skor: {sc:.1f}). Varlıkta {reason_str}. Ancak henüz tam bir güvenli kırılım (breakout) teyidi alamadığım için eyleme geçmeden beklemedeyim."
            
            # Cooldown 15 saniyeye düşürüldü, akış sürekli devam edecek.
            logger.info(f"[THOUGHT STREAM] Adding thought for {sym} to bot_thought_stream. Score: {sc}")
            bot_thought_stream.add_throttled("🧠 Astra-6 Analitiği", sym, thought, "INFO", cooldown_sec=15)
        else:
            # En iyi aday bulunamadı (Tüm varlıklar kalkanlara takıldı veya fırsat yok)
            open_pos_count = len(live_trade_manager.positions)
            if open_pos_count >= 12:
                bot_thought_stream.add_throttled("🤖 ASTRA AI (Portföy Dolu)", "SİSTEM", f"Portföy kapasitesi tam dolu ({open_pos_count}). Yeni sinyal aramıyorum, mevcut kârları maksimize etmeye ve yönetmeye odaklandım.", "INFO", cooldown_sec=60)
            else:
                bot_thought_stream.add_throttled("🤖 ASTRA AI (Pusu Modu)", "SİSTEM", "Şu an piyasada kayda değer bir fırsat veya momentum göremiyorum. Filtrelerimden geçen kaliteli bir kurulum yok, sabırla pusu modunda bekliyorum.", "INFO", cooldown_sec=60)
                
        return executed_triggers

tv_auto_runner = TradingViewAutoStrategyRunner()

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
from services.engine.ha_manager import ha_manager
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
from services.intelligence.yuce_divan_oracle import yuce_divan
from services.intelligence.active_trade_reporter import active_trade_reporter
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
                import traceback
                logger.error(f"[AUTO-RUNNER ERROR] {e}\n{traceback.format_exc()}")
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
            bot_thought_stream.add_throttled(
                "🔥 MAKRO KARARTMA KİLİDİ", "GLOBAL", 
                f"Admin, FED toplantısı veya kritik makroekonomik veri açıklaması var. Piyasa yapıcıların manipülasyonundan (Whipsaw) korunmak için tüm alımları geçici olarak durdurdum. Sadece açık pozisyonların TP/SL süreçlerini yönetiyorum. Neden: {blackout_reason}", 
                "WARNING", cooldown_sec=600
            )
            return []

        now_ts = time.time()
        self.last_evaluated_signals = {
            k: v for k, v in self.last_evaluated_signals.items()
            if now_ts - v < self.SYMBOL_COOLDOWN_SECONDS
        }

        # F&G: Block yerine lot cezası
        import asyncio
        fg_assessment = await asyncio.to_thread(fear_greed_client.get_assessment)
        fg_lot_penalty = 0.5 if fg_assessment.should_block else 1.0
        if fg_assessment.should_block:
            logger.warning(f"[F&G SOFT] Aşırı açgözlülük — lot x0.5, alım devam ediyor.")

        market_data_raw_unfiltered = await asyncio.to_thread(tradingview_live_client.fetch_live_market_data)
        
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

        # === ERKEBİŞİM YARIŞI (SNIPER RACE KEY) — KOMİTE REVİZYONU ===
        # HATA TESPİTİ: Eski race key yüksek RSI'ı önce alıyordu = FOMO sıralaması!
        # YENİ: Erken Giriş felsefesi. RSI 40-55 = ideal avcı bölgesi = kuyruğun BAŞI.
        # RSI 55-68 = orta, RSI > 68 = sona atılır. Hacim tiebreaker olarak kalır.
        def _rsi_race_key(item):
            sym, d = item
            rsi_val  = float(d.get("rsi", 0.0) or 0.0)
            vol_val  = float(d.get("volume_ratio", 0.0) or 0.0)
            chg_val  = float(d.get("change_pct", 0.0) or 0.0)
            # RSI 40-55 ideal bölgesi için ters çevirme: 100 - rsi_val ile uzaklığı ölç
            # RSI 50 => uzaklık = 5 (50'ye en yakın en yüksek puan alır)
            rsi_early_score = 10.0 - abs(rsi_val - 50.0) * 0.3
            # Birleşik yarış skoru: Erken RSI önce, hacim tiebreaker
            return rsi_early_score + vol_val * 5.0 + chg_val * 1.0

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
                        bot_thought_stream.add_throttled("🧠 Otonom Zeka", v_sym, f"[{v_sym}] {thought}", "SUCCESS", cooldown_sec=600)
                        
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
                        bot_thought_stream.add_throttled("🧠 Otonom Zeka", v_sym, f"[{v_sym}] {thought}", "WARNING", cooldown_sec=600)
                        
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

            # HUNTER: AŞIRI-UÇ FOMO'YU ENGELLE — KOMİTE SIKILEŞME KARARI
            # Eski: RSI>90 + chg>10% (çok gevşek, RSI=89+%9.5 bile geçiyordu)
            # Yeni: RSI>85 + chg>7.0% (daha gerçekçi ve erken engelleme)
            if rsi > 85.0 and chg_pct >= 7.0:
                logger.info(f"[FOMO HARD] {sym} RSI={rsi:.0f}+CHG={chg_pct:.1f}% — aşırı FOMO pump, atlanıyor.")
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
            open_positions_list = [p for p in live_trade_manager.positions.values() if p.status == "OPEN"]

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
            # RANGING: Block
            if regime_result.should_skip_momentum:
                logger.info(f"🚫 [REGIME STRICT] {sym} RANGING/Kararsız rejim tespit edildi. Momentum yok, işlem pas geçiliyor.")
                continue

            # FAKEOUT GUARD: Hard Block→-2 skor cezası
            _candle_range = candle_high - candle_low
            _candle_body  = abs(price - candle_open)
            _body_ratio_early = (_candle_body / _candle_range) if _candle_range > 0 else 0.5
            fakeout_res = fakeout_guard.check(
                symbol=sym, price=price, change_pct=chg_pct, vol_ratio=vol_ratio,
                rsi=rsi, cmf=cmf, stoch_k=stoch_k, atr_pct=atr_pct,
                body_ratio=_body_ratio_early, bid_ask_ratio=bid_ask_ratio
            )
            if fakeout_res.is_fakeout:
                logger.info(f"🚫 [FAKEOUT STRICT] {sym}: {fakeout_res.reason} — Sahte Kırılım Tespit Edildi, İşlem İptal.")
                continue

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
            
            # ÖNERİ 1: MTF (Multi-Timeframe) Makro Trend Filtresi / Kalkanı
            # Not: Sinyaldeki 200 EMA ile fiyatı kıyaslayıp makro (büyük) trendi buluyoruz
            is_crypto = sym.endswith("USDT") or sym in ["BTC", "ETH", "SOL", "BNB"]
            if is_crypto:
                ema_200 = float(data.get("ema200") or 0.0)
                if ema_200 > 0.0:
                    dist_to_ema200 = ((price - ema_200) / ema_200) * 100.0
                    if dist_to_ema200 < -3.0:
                        score -= 4.0
                        logger.warning(f"📉 [MTF MAKRO TREND] {sym} Ana Trend Çok Kötü (200-EMA'nın %{abs(dist_to_ema200):.1f} altında). Düşen Bıçak Kalkanı -> -4 Puan Cezası")
                    elif dist_to_ema200 > 1.5:
                        score += 3.0
                        logger.info(f"📈 [MTF MAKRO TREND] {sym} Ana Trend Çok Güçlü (200-EMA'nın %{dist_to_ema200:.1f} üstünde). Rüzgar Arkamızda -> +3 Puan Bonusu")


            # === ATR BAZLI DINAMIK TP/SL + REJIM MATRISI ===
            is_crypto = sym.endswith("USDT") or sym in ["BTC", "ETH", "SOL", "BNB"]
            is_mean_reversion_buy = False
            is_arbitrage_buy = False
            atr_absolute = price * (atr_pct / 100.0)

            # Rejim Motorunu guncelle (sadece her 60s'de bir tam hesapla)

            if time.time() - regime_engine._last_update > 60:
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
                "vwap":         2 if mkt_type == "NASDAQ" else 3,  # MTF sonrası VWAP teyidi çok daha değerli (Kripto +3)
                "volume_surge": 3.5 if mkt_type == "CRYPTO" else 1.5, # Hacim teyidinin Kripto çarpanı artırıldı
                "volume_norm":  1.0,
                "adx":          1.5 if mkt_type == "NASDAQ" else 2.5, # MTF sonrası trend onayı çok güvenilir (Kripto +2.5)
            }

            # I1: RSI - ERKEN KIRILIM VE DİPTEN YAKALAMA PRENSİBİ (Late Entry Kalkanı)
            # Kullanıcı isteği: Patlamış varlıklara değil, dipten toparlanan veya patlamaya hazır (RSI 40-55) varlıklara odaklan.
            if 25.0 <= rsi <= 35.0:
                score += 4.0  # Aşırı satım (Dip bölgesi) - Büyük Fırsat (Aşağıdan alma)
                logger.debug(f"[I1 RSI] {sym} RSI={rsi:.1f} dip bölgesi (Aşırı satım) -> +4.0 (Erken keşif)")
            elif 35.0 < rsi <= 50.0:
                score += 3.0 # Erken toparlanma fazı
                logger.debug(f"[I1 RSI] {sym} RSI={rsi:.1f} dipten dönüş / potansiyel patlama -> +3.0")
            elif 50.0 < rsi <= 60.0:
                score += 1.5
                logger.debug(f"[I1 RSI] {sym} RSI={rsi:.1f} erken kırılım bandı -> +1.5")
            elif 60.0 < rsi < 68.0:
                score -= 1.0 # Artık trend olgunlaştı, iğne riski
                logger.debug(f"[I1 RSI] {sym} RSI={rsi:.1f} olgun trend (iğne yeme riski başlıyor) -> -1.0")
            elif rsi >= 68.0:
                # Kesin şişkinlik ve iğne yeme ihtimali çok yüksek
                if adx >= 35.0 and vol_ratio >= 2.0 and chg_pct < 2.0:
                    score += 1.0
                    logger.info(f"🔥 [I1 RSI MOMENTUM] {sym} RSI={rsi:.1f} ama CHG henüz düşük, Hacim coşmuş! Kırılım -> +1.0")
                else:
                    score -= 6.0
                    logger.warning(f"[I1 RSI - ÖNDEN DÜŞÜN KALKANI] {sym} RSI={rsi:.1f} YORGUN/ŞİŞKİN! Tepeden girme riski -> -6.0")

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
                hh_bonus = 4 if mkt_type == "CRYPTO" else 1.5  # MTF sonrası 15m+1h Higher High çok zor kırılır, ödülü +4
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
                ob_bonus = 3 if mkt_type == "CRYPTO" else (2 if mkt_type == "NASDAQ" else 1) # Kripto'da alıcı üstünlüğü sağlam ödüllendirildi
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
                # KOMİTE KARARI REVİZYONU: Kripto'da %4 çok dar olabilir, gerçek bir ralli yeni başlıyor olabilir. 
                # Kripto için sınır %6.0, Hisse için %3.0 olarak esnetildi. (Kullanıcı +2 Opsiyonu)
                pump_threshold = 6.0 if is_crypto else 3.0
                
                if chg_pct >= pump_threshold:
                    score -= 10 # KESİN İPTAL - GEÇ KALINDI
                    logger.warning(f"[I13 TEPEDEN ALMA KORUMASI] {sym} ZATEN PATLAMIŞ (Değişim: %{chg_pct:.2f}). Zirveden maliyetlenmemek için İPTAL -> -10 Ceza")
                elif vol_ratio >= 2.5 and chg_pct >= (pump_threshold * 0.7):
                    score -= 2
                    logger.warning(f"[I13 PUMP RİSKİ] {sym} AŞIRI HACİM VE YÜKSELİŞ: vol={vol_ratio:.2f} chg={chg_pct:.2f}% -> -2 Ceza (İğne Yeme Riski Aktif)")
                else:
                    score += 5 # Kripto'da sağlam kırılım teyidi eskisinden çok daha güvenilir
                    logger.info(f"[I13 MOM] {sym} Erken Hacim+Değişim kırılım onayı -> +5 (Score: {score})")

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

            # Giris izni kontrolu (Katı Otonom)
            if not _rp["entry_allowed"]:
                logger.info(f"🚫 [REGIME STRICT] {sym} ({_mtype_local}) {_rp['regime']} rejiminde giriş yasaktır. İşlem iptal.")
                continue

            # --- TIER-2 OTONOM KONSEY (DYNAMIC THRESHOLDS) ---
            from services.engine.autonomous_council import autonomous_council
            dyn_conf = autonomous_council.current_state.get("min_confidence", 65)
            dyn_vol_adj = autonomous_council.current_state.get("min_volume_ratio", 1.0)

            # KULLANICI EMRİ: ÇARPIŞMALARI KATI HALE GETİR VE SADECE EN İYİ FIRSATLARI AL
            # Skor eşiğini tekrar kurumsal düzeye çekiyoruz.
            required_score = _rp["min_score"] + 5.0  # Ortalama 5.0 + 5.0 = 10.0 baraj.
            
            # KONSEY KARARI: HİSSE SENEDİ İÇİN DENGELİ ESNETME
            # Hisseler kripto kadar hızlı skor alamaz, ancak tamamen de serbest bırakamayız.
            if not is_crypto:
                required_score -= 1.0  # Hisselerde baraj ~9.0 puana düşer. Yarı katı.
                logger.debug(f"[KONSEY KATI MOD] {sym} Hisse Senedi. Eşik Değeri: {required_score}")
            
            # Dinamik Volatilite Barajı (Volatility Adaptive Threshold)
            if is_crypto:
                if atr_pct > 3.5:
                    required_score += 1.5
                    logger.debug(f"[VIX/ATR KORUMASI] {sym} Volatilite çok yüksek (ATR: %{atr_pct:.2f}). Fiyatın oturması bekleniyor. Baraj zorlaştırıldı: {required_score}")
                elif atr_pct < 1.5:
                    required_score -= 1.0
                    logger.debug(f"[VIX/ATR FIRSATI] {sym} Piyasa sakin (ATR: %{atr_pct:.2f}). Kırılımlar daha temiz. Baraj esnetildi: {required_score}")

            min_vol           = max(0.1, _rp["min_vol"] * 0.5) * dyn_vol_adj
            global_max_pos    = 10 # Normal kapasite 10
            max_pos_for_market_regime = _rp["max_market_pos"] + 1
            
            # Temporal sl_tighten_pct ile stop-loss mesafesini dinamik olarak daralt
            # Kâr-Al Hedefi (Dinamik İz Sürücü ve ML'e bırakıldı)
            base_tp = _rp["tp_pct"]
            try:
                base_sl = _rp["sl_pct"] * temp_mods.get("sl_tighten_pct", 1.0)
            except:
                base_sl = _rp["sl_pct"]

            # =========================================================
            # 🥷 SESSİZLİK PATLAMASI (VCP - Squeeze) TESPİTİ
            # =========================================================
            is_vcp = False
            # KOMİTE GÜVENLİK REVİZYONU: VCP bonusu +30'dan +18'e indirildi.
            # Gerekçe: +30 puan RSI cezası (-6) ve pump cezası (-10) dahil TÜM filtreleri geçersiz kılıyordu.
            # +18 ise sadece gerçek VCP sinyalini yeterince ödüllendirir, sahte durumları da frenler.
            # Ek koruma: ADX < 20 koşulu eklendi (trend yoksa hacimsizlik gerçekten VCP'dir).
            if vol_ratio < 0.6 and 40.0 <= rsi <= 60.0 and abs(chg_pct) <= 1.0 and adx < 25.0:
                is_vcp = True
                score += 18.0  # VCP Avcı Bonusu (Güvenli seviyeye indirildi - Komite Kararı)
                logger.info(f"🥷 [VCP HUNTER] {sym} Sessizlik Patlaması (Squeeze) hazırlığı algılandı! Pusuya yatılıyor (+18 Puan - Güvenli Mod).")
                bot_thought_stream.add_throttled(
                    "🥷 VCP Patlama Pususu", sym, 
                    f"Admin, VCP (Volatilite Daralması) formasyonu saptadım. Hacim {vol_ratio:.2f} seviyesine kadar kurumuş fakat fiyatın altına inilmiyor. ADX de trend yok diyor. Sessizlik patlaması bekliyorum, radarıma alıp pusuya yatıyorum.", 
                    "SUCCESS", cooldown_sec=300
                )

            # =========================================================
            # 🔮 ÖNGÖRÜ (FORESIGHT) & GİZLİ BALİNA TESPİTİ (Erken Atlayış)
            # =========================================================
            is_foresight_early_jump = False
            # [KONSEY REVİZYONU]: Hacim şişmesi (vol_ratio) tek başına yeterli değil, bu bir satış hacmi olabilir (Dump).
            # Güvenlik Kontrolleri:
            # 1. 0 <= chg_pct < 1.5 -> Fiyat eksiye düşmemiş, yatay veya hafif yeşil.
            # 2. bid_ask_ratio >= 0.55 -> Giren devasa hacim, ALICI (Buy Wall) baskısı. Satış değil!
            # 3. 55 <= rsi <= 68 -> Trend momentumu boğa tarafında tırmanışa geçmiş.
            if 0.0 <= chg_pct < 1.5 and vol_ratio >= 1.5 and 55.0 <= rsi <= 68.0 and bid_ask_ratio >= 0.55:
                is_foresight_early_jump = True
                score += 15.0  # +15 çok güçlü bir itici güçtür ama ML veya Direnç bloklarını (Trap) tamamen körü körüne delmez.
                logger.info(f"🔮 [FORESIGHT PRE-BREAKOUT] {sym} Piyasadan önce balina ALIMI saptandı (Bid/Ask: %{bid_ask_ratio*100:.1f})! Erkenden atlanıyor (+15 Puan).")
                bot_thought_stream.add_throttled(
                    "🔮 Öngörü & Gizli Balina", sym, 
                    f"Admin, {sym} tahtasında fiyat henüz hareket etmemiş (Chg: %{chg_pct:.2f}) ancak derinlikte balina alımları seziyorum (Bid:%{bid_ask_ratio*100:.0f}). Gerçek kırılım gelmeden önce ön saflarda yerimi alıyorum.", 
                    "SUCCESS", cooldown_sec=300
                )

            # =========================================================
            # 🌑 KARANLIK HAVUZ (DARK POOL) AKÜMÜLASYON DEDEKTÖRÜ
            # =========================================================
            is_dark_pool = False
            # Fiyat adeta donmuş (-0.5 ile +0.5 arası) ancak hacim son 20 mumun 5 KATINDAN FAZLA!
            # Bu durum perakende (küçük) yatırımcı olamaz, devasa OTC (tezgah altı) kurumsal balina alımıdır.
            if abs(chg_pct) <= 0.5 and vol_ratio >= 5.0 and rsi < 65.0:
                is_dark_pool = True
                score += 30.0  # Çok nadir ve kesin bir fırsat! Kesin Onay (Sniper)
                logger.info(f"🌑 [DARK POOL DETECTED] {sym} tahtasında fiyat sabit ama Hacim {vol_ratio}x patladı! Kurumsal Akümülasyon seziyorum (+30 Puan).")
                bot_thought_stream.add_throttled(
                    "🌑 Karanlık Havuz (Dark Pool)", sym, 
                    f"Komutanım, {sym} tahtasında inanamayacağınız bir anormallik var. Fiyat yatay (%{chg_pct:.2f}) ama hacim normalin {vol_ratio:.1f} KATI! Devasa bir fon veya kurumsal balina kimseye çaktırmadan mal topluyor. Radarı delip geçiyorum!", 
                    "SUCCESS", cooldown_sec=600
                )

            # =========================================================
            # ⚡ ŞİMŞEK ÇÖKÜŞ (FLASH CRASH) V-RECOVERY AVCISI
            # =========================================================
            is_flash_crash = False
            # Sadece kriptoda geçerli. Kısa sürede %10'dan fazla çakılan, RSI'ı 20'nin altına inen tasfiye (liquidation) iğneleri.
            if is_crypto and chg_pct <= -10.0 and rsi <= 20.0 and vol_ratio >= 2.0:
                is_flash_crash = True
                score += 50.0 # Tüm teknik düşüş cezalarını (Düşük MACD vb.) ezip geçer
                logger.warning(f"⚡ [FLASH CRASH HUNTER] {sym} Piyasada Şimşek Çöküş (-%{abs(chg_pct):.1f}) var! Korkmak yerine tasfiye (liquidation) iğnesine ağ atıyorum (+50 Puan)!")
                bot_thought_stream.add_throttled(
                    "⚡ Şimşek Çöküş Avı", sym, 
                    f"{sym} aniden %{abs(chg_pct):.1f} çöktü. Korkup kaçmak yerine bu haksız tasfiye (liquidation) iğnesine pusu kuruyorum. V-Recovery (V şeklinde toparlanma) bekliyorum!", 
                    "WARNING", cooldown_sec=600
                )

            # Soft cezalar (fakeout, pullback vs) Yüce Divan (Strict Mode) kapsamında iptal edildiği için skor manipülasyonu kaldırıldı.
            pass

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
                            logger.warning(f"🚫 [TRAP STRICT] {sym} Bull Trap ihtimali çok yüksek! Tuzaktan kaçılıyor.")
                            continue
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

                if ml_prob < 0.30:
                    msg = f"🚫 [TOXIC FLOW DETECTED] ML Modeli {sym} için kazanma ihtimalini %{ml_prob*100:.1f} olarak hesapladı. (Fakeout Riski). İşlem Reddedildi."
                    logger.warning(msg)
                    try:
                        experience_memory_engine.add_live_log(_mtype_local, "BLOCK", msg)
                    except: pass
                    continue
                
                if ml_prob >= 0.70: 
                    bot_thought_stream.add_throttled("🧠 Otonom Onay (Tier-1)", sym, f"Admin, temel filtreleri geçtik. Makine Öğrenimi (ML) motorum bu setup'ı inceledi ve kazanma ihtimalimizi %{ml_prob*100:.0f} olarak onayladı. Kasa yönetimine (Router) aktarıyorum.", "SUCCESS", cooldown_sec=180)
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
                
                if alpha_val <= -0.80 and not is_vcp:
                    msg = f"🚫 [ALPHA REJECT] {sym} Kurumsal Analist motoru bu harekette 'Fakeout/Spoofing' tespit etti (Alpha: {alpha_val:.2f}). İşlem engellendi."
                    logger.warning(msg)
                    try:
                        experience_memory_engine.add_live_log(_mtype_local, "BLOCK", msg)
                    except: pass
                    continue
                elif alpha_val <= -0.60 and not is_vcp:
                    # Orta risk: skoru düşür ama engelleme
                    score += (alpha_val * 3.0)  # -0.6*3 = -1.8 ceza, işlem devam eder
                    logger.info(f"⚠️ [ALPHA SOFT WARN] {sym} Alpha zayıf ({alpha_val:.2f}). Skor düşürüldü, işlem devam ediyor.")
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
                # 3X ŞARJÖR AKTİF: ML skoru > %85 ise Kelly Kriterini agresif ez!
                if _mtype_local == "CRYPTO" and ml_prob >= 0.85:
                    kelly_mult = 3.0
                    logger.info(f"🔫 [3X ŞARJÖR AKTİF] {sym} için ML Kazanma İhtimali olağanüstü yüksek (>%85). Kelly Çarpanı 3'e katlandı!")

                kelly_impact = (kelly_mult - 1.0) * 3.0
                score += kelly_impact
                
                if kelly_impact != 0:
                    logger.info(f"⚖️ [KELLY RISK ANALYST] Genel Kelly Çarpanı: {kelly_mult:.2f} -> Güven Skoruna Etkisi: {kelly_impact:+.1f} Puan")
                    
                if kelly_mult <= 0.3:
                    bot_thought_stream.add_throttled("⚖️ Defans Modu", sym, "Kelly Kriteri çok düşük. Kasa koruma amacıyla puanlar baskılanıyor.", "WARNING", cooldown_sec=180)
            except Exception as kelly_err:
                pass

            if not is_crypto:
                logger.info(f"📊 [NASDAQ RADARI] {sym} | Skor: {score} | İstenen Baraj: {required_score} | Fiyat: {price}")


            # KOMİTE GÜVENLİK REVİZYONU: ML ve Alpha Bypass artık RSI+Pump güvencesiyle çalışır!
            # HATA TESPİTİ: ml_prob >= 0.70 tüm RSI cezaları ve pump korumalarını bypass ediyordu.
            # Örnek: RSI=80, chg=%8 bir varlık ML=%72 olursa ALIM yapılıyordu = iğne yeme garantisi.
            # YENİ: ml_prob bypass sadece RSI < 68 VE chg < pump_threshold olan varlıklarda çalışır.
            alpha_bypass = ('alpha_val' in locals() and alpha_val >= 0.75)
            _pump_thr_check = 6.0 if is_crypto else 3.0
            _ml_bypass_safe = (rsi < 68.0) and (chg_pct < _pump_thr_check)  # RSI ve pump güvencesi
            is_buy_signal = (score >= required_score) or (ml_prob >= 0.70 and _ml_bypass_safe) or alpha_bypass
            
            if is_buy_signal:
                # EKLENTİ 1: CUMA SENDROMU (Weekend Macro-Liquidation) Muhafızı
                from datetime import datetime
                import pytz
                now_tr = datetime.now(pytz.timezone('Europe/Istanbul'))
                # Eğer Gün Cuma ise (weekday() == 4) ve saat 21:00'den sonraysa
                is_friday_night = (now_tr.weekday() == 4) and (now_tr.hour >= 21)
                
                # Sadece Kripto için Pazar gecesi kapanış sendromu (Asya açılışı şoku)
                is_sunday_night = (now_tr.weekday() == 6) and (now_tr.hour >= 23)
                
                if (is_friday_night and not is_crypto) or (is_sunday_night and is_crypto):
                    logger.warning(f"🛡️ [CASH IS KING] {sym} için fırsat muazzam ancak 'Hafta Sonu Risk Sendromu' devrede. İşlem REDDEDİLDİ. Nakit korunuyor.")
                    is_buy_signal = False
                    try:
                        bot_thought_stream.add_throttled("🛡️ HAFTA SONU KORUMASI", sym, "Fırsat var ancak Cuma Kapanış / Pazar Gece likidasyon riski nedeniyle işlem iptal edildi. Nakit kraldır.", "WARNING", cooldown_sec=300)
                        experience_memory_engine.add_live_log(_mtype_local, "BLOCK", "Cuma Kapanış Sendromu")
                    except: pass
                    continue
                
                # EKLENTİ 2: L2 SPOOFING (Sahte Duvar) KALKANI
                # Hacim devasa (vol_ratio >= 3.0) ama fiyat eksiye veya sıfıra çakılmışsa, tahtadaki alım duvarları sahtedir (Spoofing). Balina mal boşaltıyordur.
                is_spoofed = (vol_ratio >= 3.0) and (chg_pct <= 0.2)
                if is_spoofed:
                    logger.warning(f"🚫 [SPOOF KALKANI] {sym} tahtasında Sahte Alım Duvarı (Spoofing) tespit edildi! Hacim {vol_ratio}x ama fiyat baskılanıyor. İşlem REDDEDİLDİ.")
                    is_buy_signal = False
                    try:
                        bot_thought_stream.add_throttled("🚫 SPOOF TESPİTİ", sym, f"Balinalar devasa sahte emirler girdi (Hacim: {vol_ratio}x). Tuzak fark edildi, işlem iptal edildi.", "ERROR", cooldown_sec=300)
                        experience_memory_engine.add_live_log(_mtype_local, "BLOCK", "Sahte Emir (Spoofing) Tuzağı")
                    except: pass
                    continue

                # EKLENTİ 3: Kırmızı Bayrak (Red Flag - Haber/Scam/Hack) Kilidi
                from services.risk_engine.red_flag_guardian import red_flag_guardian
                # Gerçek veri akışı bağlandığında data["latest_news"] üzerinden beslenecek.
                mock_recent_news = data.get("latest_news_headline", "")
                rf_res = red_flag_guardian.check_red_flags(sym, mock_recent_news)
                if not rf_res["is_safe"]:
                    logger.warning(rf_res["reason"])
                    is_buy_signal = False
                    try:
                        bot_thought_stream.add_throttled("🚨 KIRMIZI BAYRAK", sym, rf_res["reason"], "ERROR", cooldown_sec=300)
                        experience_memory_engine.add_live_log(_mtype_local, "BLOCK", rf_res["reason"])
                    except: pass
                    continue # Teknik körlük tuzağından kaçıldı, sinyal iptal edildi.
            
            if alpha_bypass and not (score >= required_score):
                logger.info(f"💎 [VIP BYPASS] {sym} Kurumsal Alpha çok yüksek ({alpha_val:.2f}). Teknik baraj (Skor: {score:.1f}) aşıldı!")
            if ml_prob >= 0.70 and not _ml_bypass_safe:
                logger.warning(f"[ML BYPASS BLOKLANDI] {sym} ML=%{ml_prob*100:.0f} yüksek ancak RSI={rsi:.1f} veya chg=%{chg_pct:.1f} güvensiz. Bypass reddedildi. (Tepeden alma koruması)")

            # Hacim filtresi (Korku Zinciri Kırıldı)
            vol_penalty = 1.0
            if vol_ratio < min_vol and not is_vcp:
                if is_buy_signal:
                    vol_penalty = 0.8
                    bot_thought_stream.add_throttled(
                        "🔥 Özgüvenli Giriş", sym,
                        f"[{sym}] Hacim standardın altında ({vol_ratio:.2f}) ama fırsat kaçırılamaz (Skor {score}). Analiz felci çözüldü, risk alınıyor!",
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
            # Piyasa bazında maksimum pozisyon limiti: Kripto için 4 (Konsey kararı: Az ama öz), NASDAQ için 12
            max_pos_for_market = 4 if _mtype_local == "CRYPTO" else 12
            
            # YEDEK İNİSİYATİF (4+2 Kripto Kuralı): Kullanıcı onayıyla, eğer fırsat kusursuzsa (score >= 23 veya ai_confidence > 0.74) +2 kapasite tanınır.
            # NOT: Puan sınırı 33'ten 23'e düşürüldü çünkü yeni 'Sniper/Erken Giriş' mantığı FOMO şişkinliğini sildiği için skorlar deflasyona uğradı.
            is_perfect_opportunity = score >= 23.0 or ml_prob > 0.74
            if is_perfect_opportunity and _mtype_local == "CRYPTO":
                max_pos_for_market += 2
                
            if open_pos_in_market >= max_pos_for_market:
                slot_cleared = False
                
                # TIER-1 ÇÖZÜM: ACIMASIZ ZAMAN AŞIMI VE ROTASYON (TIME-DECAY LIQUIDATION)
                # Dışarıdaki fırsat devasa ise (score >= 22 veya ml_prob > 0.76) ve içerideki tahta 4 saattir ölü taklidi yapıyorsa ACIMASIZCA KES.
                if score >= 22.0 or ml_prob > 0.76:
                    current_time_ms = int(time.time() * 1000)
                    for pos_id, pos in list(live_trade_manager.positions.items()):
                        if pos.status == "OPEN" and pos.market == _mtype_local:
                            pos_age_hours = (current_time_ms - pos.entry_timestamp_ms) / (1000 * 60 * 60)
                            pnl_pct = getattr(pos, 'unrealized_pnl_pct', 0.0)
                            
                            # EĞER POZİSYON 4 SAATTEN UZUN SÜREDİR AÇIKSA VE YATAYA BAĞLADIYSA (-%2 ile +%1 arası)
                            if pos_age_hours >= 4.0 and -2.0 <= pnl_pct <= 1.0:
                                logger.info(f"🔪 [TIER-1 ROTATION] {pos.symbol} {pos_age_hours:.1f} saattir ölü. Dışarıdaki {sym} fırsatı için kurban ediliyor!")
                                bot_thought_stream.add_throttled(
                                    "🔪 Otonom Rotasyon (Kurban)", sym,
                                    f"- Admin]: Dışarıdaki **{sym}** fırsatı o kadar büyük ki, içeride 4 saattir hareketsiz yatan **{pos.symbol}** tahtasını ufak zararına bakmadan acımasızca kapattım. Kan değişimi şart!",
                                    "WARNING", cooldown_sec=60
                                )
                                # Pozisyonu zararına (veya kârına) bakmadan sat
                                try:
                                    live_trade_manager.close_position(pos.id, "CLOSED_FOR_ROTATION")
                                    slot_cleared = True
                                    open_pos_in_market -= 1
                                    break # Sadece 1 tane kurban yeterli
                                except Exception as e:
                                    logger.error(f"Rotasyon satışı başarısız: {e}")

                if not slot_cleared:
                    msg = f"[MARKET LIMIT BLOCK] {sym} reddedildi. {_mtype_local} için maksimum ({open_pos_in_market}/{max_pos_for_market}) açık pozisyon limitine ulaşıldı."
                    logger.info(msg)
                    bot_thought_stream.add_throttled(
                        "🛡️ Kalkanlar Devrede", sym,
                        f"- Admin]: <span style='color:#f59e0b; font-weight:bold;'>{sym}</span> için {_mtype_local} kotamız dolu ({open_pos_in_market}/{max_pos_for_market}). İçeride feda edilecek (rotasyonluk) zayıf tahta da yok. Bekliyoruz.",
                        "INFO", cooldown_sec=300
                    )
                    try:
                        live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Market Limit")
                    except Exception:
                        pass
                    continue

            # SİSTEM GENELİ MAKSİMUM POZİSYON LİMİTİ (GLOBAL LIMIT BLOCK)
            # DÜZELTME: total_open_pos tüm pazarları birlikte sayıyordu.
            # Bu yüzden 12 NASDAQ pozisyonu açıkken CRYPTO sinyalleri de "12/10 dolu" diye reddediliyordu.
            # Şimdi her pazar kendi limitiyle karşılaştırılıyor.
            if _mtype_local == "CRYPTO":
                market_open_pos = sum(1 for p in live_trade_manager.positions.values() if p.status == "OPEN" and p.market == "CRYPTO")
                crypto_max = int(getattr(settings, "crypto_max_positions", 6))
                current_max = crypto_max
            else:
                market_open_pos = sum(1 for p in live_trade_manager.positions.values() if p.status == "OPEN" and p.market != "CRYPTO")
                # Dinamik Esneme: 12 max, ama fırsat çok güçlüyse +2 yedeği kullan (Max 14)
                _ml_global_bypass_safe = (rsi < 68.0) and (chg_pct < _pump_thr_check)
                current_max = 14 if (score >= required_score + 2 or (ml_prob >= 0.70 and _ml_global_bypass_safe)) else 12

            total_open_pos = market_open_pos  # Loglarda pazar bazlı göster

            if market_open_pos >= current_max:
                msg = f"[GLOBAL LIMIT BLOCK] {sym} reddedildi. {_mtype_local} için maksimum ({market_open_pos}/{current_max}) açık pozisyon limitine ulaşıldı."
                logger.info(msg)
                bot_thought_stream.add_throttled(
                    "🚧 Global Limit", sym,
                    f"- Admin]: <span style='color:#10b981; font-weight:bold;'>{sym}</span> radarımda ama <b>{_mtype_local}</b> portföy limiti dolu ({market_open_pos}/{current_max}). Nakit koruması aktif, izlemekle yetiniyorum.",
                    "WARNING", cooldown_sec=300
                )
                try:
                    experience_memory_engine.add_live_log(_mtype_local, "BLOCK", msg)
                    live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Global Limit")
                except Exception:
                    pass
                continue


            # BÜTÇE LİMİT KONTROLÜ (Yalıtılmış Bütçe Mimarisi)
            is_crypto = _mtype_local == "CRYPTO"
            if is_crypto:
                total_invested = sum(
                    p.nominal_value for p in live_trade_manager.positions.values()
                    if (p.status == "OPEN" or (p.status == "PENDING_BROKER" and p.broker_order_id)) and p.market == "CRYPTO"
                )
                active_budget_limit = float(settings.crypto_paper_budget)
            else:
                total_invested = sum(
                    p.nominal_value for p in live_trade_manager.positions.values()
                    if (p.status == "OPEN" or (p.status == "PENDING_BROKER" and p.broker_order_id)) and p.market != "CRYPTO"
                )
                active_budget_limit = 8000.0  # Alpaca (Hisse) bütçesi

            if total_invested >= active_budget_limit:
                if score >= required_score + 3.0:
                    logger.info(f"💎 [BUDGET OVERRIDE] {sym} Bütçe sınırında ancak efsanevi fırsat (Skor {score}). Minimal lot (x0.3) ile dahil olunuyor.")
                    bot_thought_stream.add_throttled(
                        "💎 Bütçe Kısıtlı Ama Fırsat Büyük", sym, 
                        f"Admin, {active_budget_limit}$ yalıtılmış bütçe tavanına ulaştık ama sistem nadir görülen {score:.1f} puanlık bir volatilite yakaladı. Güvenlik kurallarını esnetip riski x0.3'e düşürerek bu fırsatı portföye sızdırıyorum.", 
                        "SUCCESS", cooldown_sec=300
                    )
                    vol_penalty *= 0.3
                else:
                    msg = f"[BUDGET LIMIT BLOCK] {sym} reddedildi. {active_budget_limit}$ bütçe limitine ulaşıldı."
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
                # 🧠 ML DESTEKLİ DİNAMİK AKILLI ÇIKIŞ (Smart Exit)
                if open_pos.unrealized_pnl_pct >= 1.0:
                    # Kâr %3'ü geçtiyse ML'in en ufak şüphesinde (Win: < %50) karı cebe al
                    if open_pos.unrealized_pnl_pct >= 3.0 and ml_prob < 0.50:
                        logger.info(f"🧠 [ML SMART EXIT] {sym} %{open_pos.unrealized_pnl_pct:.2f} kârda. ML kazanma ihtimalini %{ml_prob*100:.1f} hesapladı (Trend Soğuması). Kâr güvenceye alınıyor.")
                        live_trade_manager.close_position(open_pos.id, "CLOSED_EARLY_ML")
                    # Kâr %1-3 arasıysa sadece sert kırılımlarda (Win < %35) veya RSI göçtüğünde çık
                    elif ml_prob < 0.35 or (rsi < 45.0 and cmf < -0.10):
                        logger.info(f"🧠 [ML SMART EXIT] {sym} %{open_pos.unrealized_pnl_pct:.2f} kârda. Sert trend kırılımı tespit edildi (ML Win: %{ml_prob*100:.1f}, RSI: {rsi}).")
                        live_trade_manager.close_position(open_pos.id, "CLOSED_EARLY_ML")
                continue

            # ==========================================
            # MARKET REGIME NO-TRADE KALKANI (Tier-1 Skill)
            # ==========================================
            current_regime = regime_engine.current_regimes.get(_mtype_local, "SIDEWAYS")
            if _mtype_local == "CRYPTO" and current_regime in ["SIDEWAYS", "BEAR", "CRASH"]:
                if score < (required_score + 0.5):
                    msg = f"🛡️ [REGIME GUARD] Kripto {current_regime} rejiminde. Skor ({score}) yetersiz olduğu için ALIM REDDEDİLDİ."
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
                
                # ==========================================
                # ŞARJÖR SOĞUTMA (COOLDOWN) KALKANI
                # ==========================================
                current_time = time.time()
                if not hasattr(self, "_last_trade_time"):
                    self._last_trade_time = 0

                # DİNAMİK ŞARJÖR SOĞUTMA (SNIPER COOLDOWN) — KOMİTE +2 ÖNERİSİ
                # Kripto 7/24 çalışır, fırsatlar hızlı gelip geçer -> 90sn (Çevik Sniper)
                # NASDAQ Pre/Post/RTH saatleri daha az gürültülü -> 240sn (Ölçülü Giriş)
                # BIST standart -> 180sn (Varsayılan)
                if _mtype_local == "CRYPTO":
                    _cooldown_seconds = 10
                elif _mtype_local == "NASDAQ":
                    _cooldown_seconds = 15
                else:
                    _cooldown_seconds = 10

                if (current_time - self._last_trade_time) < _cooldown_seconds:
                    remaining = int(_cooldown_seconds - (current_time - self._last_trade_time))
                    msg = f"⏳ [COOLDOWN] {sym} sinyal üretti ancak şarjör soğuma süresinde (Kalan: {remaining}sn / {_mtype_local} için {_cooldown_seconds}sn)."
                    logger.info(msg)
                    bot_thought_stream.add_throttled("⏳ Şarjör Soğutuluyor", "SYSTEM", f"Piyasanın son işlemime tepkisini ölçüyorum. {sym} fırsatı var ancak {remaining} saniye bekleyeceğim.", "WARNING", cooldown_sec=180)
                    try:
                        live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Cooldown")
                    except Exception:
                        pass
                    continue

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
                    # KONSEY KARARI: Hisselerde çakışma (conflict) daha tolere edilebilir
                    qty_mult *= (0.70 if is_crypto else 0.90)

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
                # 7'Lİ YÜCE DİVAN (ORACLE) ONAY KATMANI
                # ═══════════════════════════════════════════════════════════
                divan_result = await yuce_divan.get_council_decision(sym, score, rsi, vol_ratio)
                if not divan_result["approved"]:
                    bot_thought_stream.add_throttled("YÜCE DİVAN", sym, divan_result["admin_msg"], level="WARNING", cooldown_sec=60)
                    logger.warning(f"[YUCE DIVAN BLOCKED] {sym} -> {divan_result['admin_msg']}")
                    continue # İnfazı iptal et ve sıradaki fırsata geç
                
                # YÜCE DİVAN ONAYLADI! Ancak henüz mesaj atmıyoruz, işlemin borsada açılmasını (process_order) bekleyeceğiz.
                llm_lot_mult = 1.0
                logger.debug(f"[AUTO-RUNNER] {sym} kantitatif filtreleri ve Yüce Divan onayını geçti. İnfaz başlatılıyor.")

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

                from core.config import settings as core_settings
                
                final_qty = round(dyn_cap / price, 4)
                if final_qty <= 0.0:
                    logger.warning(f"🚨 [BUDGET SHIELD] {sym} Final Bütçe $0. Miktar 0 olduğu için pas geçiliyor.")
                    bot_thought_stream.add_throttled("CEPHANE YETERSİZ", sym, f"Komutanım, {sym} için Konsey onay verdi ancak kasada yeterli bakiye (Cephane) olmadığı için işlem AÇILAMADI!", level="ERROR", cooldown_sec=60)
                    continue

                signal = WebhookSignal(
                    passphrase=getattr(core_settings, "passphrase", "tolga_trading_key_123!"),
                    action="BUY",
                    symbol=sym,
                    price=price,
                    quantity=final_qty,
                    take_profit=target_tp_price,
                    stop_loss=target_sl_price,
                    account_equity=dyn_cap,
                    market_position="long",
                    timestamp_ms=int(time.time() * 1000),
                    indicators={
                        "rsi": rsi,
                        "volatility": atr_pct,
                        "atr_pct": atr_pct,
                        "atr_value": atr_absolute,
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
                    res = {}
                    if not ha_manager.is_leader:
                        logger.warning(f"💤 [HA STANDBY] {sym} fırsatı yakalandı (Puan: {score}/8) ancak bu Node LİDER olmadığı için işleme girilmiyor.")
                        res = {"status": "skipped", "reason": "HA_STANDBY"}
                    else:
                        res = await asyncio.to_thread(process_order, signal)
                        # BÜYÜK BUG FİXİ: Global Cooldown SADECE işlem başarıyla AÇILDIYSA tetiklenir!
                        if res.get("status") in ["success", "paper_success", "shadow_success", "ok", "executed"]:
                            self._last_trade_time = current_time
                            bot_thought_stream.add_throttled("YÜCE DİVAN", sym, divan_result["admin_msg"], level="SUCCESS", cooldown_sec=60)
                            
                            # YENİ ÖZELLİK: Komutanın istediği detaylı SAVAŞ EMRİ / HAREKAT RAPORU
                            asyncio.create_task(active_trade_reporter.generate_and_store_report(
                                symbol=sym,
                                price=price,
                                tp1=target_tp_price,
                                tp2=price * (1 + ((dyn_tp_pct * 1.5) / 100.0)), # Örnek 2. TP Hedefi
                                sl=target_sl_price,
                                action="BUY"
                            ))
                        else:
                            reason = res.get('reason', 'UNKNOWN_REASON')
                            msg_detail = res.get('message', '')
                            err_str = f"{reason}" + (f" - {msg_detail}" if msg_detail else "")
                            bot_thought_stream.add_throttled("BORSA REDDETTİ", sym, f"Konsey füzeyi ateşledi ancak borsa/broker işlemi reddetti (Hata veya limit): {err_str}", level="ERROR", cooldown_sec=60)
                            
                            # YENİ ÖZELLİK: Reddedilen işlemler de Admin paneline "Operasyon İptal Edildi" olarak düşsün
                            asyncio.create_task(active_trade_reporter.generate_and_store_report(
                                symbol=sym,
                                price=price,
                                tp1=0, tp2=0, sl=0,
                                action="BUY",
                                status="REJECTED",
                                error_msg=err_str
                            ))
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
            
            import random
            
            # Rastgele cümle kalıpları ile zenginleştirilmiş dil yapısı
            intros_high_score = [
                "Selam Admin. Piyasayı taradım ve şu an en çok dikkatimi çeken 'Potansiyel Aday' varlık",
                "Admin, algoritmalarım alarm veriyor. Şu an pusuda izlediğim ana hedef",
                "Tüm piyasayı eledim ve şu an izleme listemin (Watchlist) en tepesindeki kurulum",
                "Admin, radarıma çok güçlü bir sinyal takıldı ancak tetiğe basmak için onay bekliyorum:"
            ]
            
            intros_low_score = [
                "Admin, fırsat havuzunda henüz tam olgunlaşmamış izlemeye aldığım varlıklardan biri",
                "Şu an arka planda sessizce takip ettiğim (işlem açmadığım) tahta",
                "Piyasada henüz net bir kırılım yok, pusudayım. Sadece potansiyel gördüğüm varlık",
                "Admin, henüz tetiğe basmak için erken, sadece gözüm üzerinde:"
            ]
            
            outros_high_score = [
                "Sahte kırılıma (fakeout) düşmemek için Yüce Divan ve bütçe (cephane) onayı bekliyorum.",
                "Hacim teyidi ve Konsey onayı geldiği an tetiğe basıp işlemi Aktif Pozisyonlara düşüreceğim.",
                "Risk/Ödül oranı şu an iyi. Karar aşamasındayım, şartlar 100% olursa işleme gireceğim.",
                "Makine Öğrenimi motorumdan son teyidi bekliyorum, onay gelirse işlem listesinde (Hedeflerde) göreceksiniz."
            ]
            
            outros_low_score = [
                "Tam bir güvenli kırılım (breakout) teyidi alamadığım için eyleme geçmeden beklemedeyim.",
                "Piyasa yapıcıların (Smart Money) ayak izlerini daha net görmem gerekiyor.",
                "Volatility düşük, bu yüzden sermayeyi riske atmak yerine izlemeyi tercih ediyorum.",
                "Şartların biraz daha olgunlaşmasını beklemek en mantıklısı."
            ]
            
            intro = random.choice(intros_high_score if sc >= 2.0 else intros_low_score)
            outro = random.choice(outros_high_score if sc >= 2.0 else outros_low_score)
            styled_sym = f"<span style='color:var(--accent-yellow); font-weight:bold;'>{sym}</span>" if sc >= 2.0 else f"<span style='color:var(--text-secondary); font-weight:bold;'>{sym}</span>"
            
            # Dinamik düşünce metni oluştur
            thought = f"{intro} {styled_sym} (YZ Skoru: {sc:.1f}/8). Bu varlıkta {reason_str}. {outro}"
            
            if sc >= 2.0:
                if sym not in self.virtual_paper_trades and sym not in live_trade_manager.positions:
                    self.virtual_paper_trades[sym] = {
                        "entry_price": best.get("price", 0.0),
                        "timestamp": now_ts,
                        "score": sc,
                        "block_reason": block_r or "teyit beklemesi",
                        "indicators": {"rsi": rsi, "volume_ratio": vol}
                    }
            
            # Sadece sembol değiştiğinde veya 120 sn geçtiğinde logla (Tekrarı önlemek için)
            if getattr(self, "_last_thought_symbol", "") != sym:
                cooldown = 15 # Sembol değiştiyse hızlı bildir
                self._last_thought_symbol = sym
            else:
                cooldown = 120 # Aynı sembolse spam yapma
            
            logger.info(f"[THOUGHT STREAM] Adding thought for {sym} to bot_thought_stream. Score: {sc}")
            bot_thought_stream.add_throttled("🧠 Zeka Motoru", sym, f"[{sym}] {thought}", "INFO", cooldown_sec=cooldown)
        else:
            # En iyi aday bulunamadı (Tüm varlıklar kalkanlara takıldı veya fırsat yok)
            open_pos_count = len([p for p in live_trade_manager.positions.values() if p.status == "OPEN"])
            if open_pos_count >= 12:
                bot_thought_stream.add_throttled("🤖 ASTRA AI (Portföy Dolu)", "SİSTEM", f"Portföy kapasitesi tam dolu ({open_pos_count}). Yeni sinyal aramıyorum, mevcut kârları maksimize etmeye ve yönetmeye odaklandım.", "INFO", cooldown_sec=60)
            else:
                bot_thought_stream.add_throttled("🤖 ASTRA AI (Pusu Modu)", "SİSTEM", "Şu an piyasada kayda değer bir fırsat veya momentum göremiyorum. Filtrelerimden geçen kaliteli bir kurulum yok, sabırla pusu modunda bekliyorum.", "INFO", cooldown_sec=60)
                
        return executed_triggers

tv_auto_runner = TradingViewAutoStrategyRunner()

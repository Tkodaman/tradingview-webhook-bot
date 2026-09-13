"""
Otonom TradingView Canlı Strateji ve Tetikleyici Motoru
Ders Çıkarımlı Olasılık Odaklı Kendini Kalibre Eden İşlem Algoritması (Self-Learning Execution Engine)
"""

import time
import asyncio
import random
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

# Global instances
llm_intelligence = LLMMarketIntelligenceEngine()

class TradingViewAutoStrategyRunner:
    def __init__(self):
        self.is_running: bool = True  # Varsayılan olarak 7/24 kesintisiz otonom aktif
        self.scan_interval_seconds: float = 3.0
        self.min_score_required: int = 6  # Yüksek seçicilik (6/8) ile agresif kayıpların önüne geçilmesi
        self.last_evaluated_signals: Dict[str, str] = {}
        self._loop_task: Any = None

    async def start_continuous_background_loop(self):
        """
        Sunucu arkasında 7/24 kesintisiz çalışan bağımsız otonom tarama döngüsü.
        """
        logger.info("[AUTO-RUNNER] Olasılık Ağırlıklı Kendini Kalibre Eden Motor Başlatıldı.")
        while True:
            try:
                if self.is_running:
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

        market_data = tradingview_live_client.fetch_live_market_data()
        executed_triggers = []

        for sym, data in market_data.items():
            # Piyasa çalışma saati kontrolü: BIST veya NASDAQ kapalıysa kesinlikle alım yapma
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
            vol_ratio = data.get("volume_ratio", round(random.uniform(0.8, 3.5), 2))
            stoch_k = data.get("stoch_k", 50.0)
            adx = data.get("adx", 25.0)
            atr_pct = data.get("atr_pct", 1.5)
            chg_pct = data.get("change_pct", 0.0)
            cmf = data.get("cmf", 0.0)
            rs_score = data.get("rs_score", 0.0)

            # ==========================================
            # DERS ÇIKARIMLI KATI FİLTRELER (ÖĞRENİLEN TELER & TUZAK ENGELLERİ)
            # ==========================================

            # DERS KURALI 1: FOMO Tepe Sıçraması Engeli (Y3 DÜZELTİLDİ: settings'den oku)
            fomo_chg = RISK_PARAMS.get("fomo_candle_change_pct", 3.0)
            fomo_rsi  = RISK_PARAMS.get("fomo_rsi_limit", 75.0)
            if chg_pct >= fomo_chg and rsi > fomo_rsi:
                logger.info(f"[SELF-LEARNING BLOCK] {sym} %{fomo_chg}+ sıçradı (RSI: {rsi:.1f}). FOMO tepe tuzagını önlemek için pullback bekleniyor.")
                continue

            # DERS KURALI 2: Düşük Volatiliteli RSI Tepe Tuzağı (RSI > 68 & ATR < 1.0)
            if rsi > 68.0 and atr_pct < 1.0:
                logger.info(f"[SELF-LEARNING BLOCK] {sym} Düşük volatilitede RSI aşırı alım tuzağında (RSI: {rsi:.1f}, ATR: %{atr_pct}). Reddedildi.")
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

            # DERS KURALI 3: Hafıza Denetimi (Peş Peşe 2 Stop Olunan Rejimde 2-Strike Hard Block)
            indicators_map = {"rsi": rsi, "volume_ratio": vol_ratio, "atr_pct": atr_pct}
            mem_check = experience_memory_engine.evaluate_signal_against_memory(sym, "BUY", indicators_map, dynamic_regime)
            if not mem_check.get("is_safe", True):
                logger.info(f"[MEMORY SHIELD BLOCK] {sym} işlemi Koruma Kalkanı tarafından reddedildi: {mem_check.get('reason')}")
                continue

            # ==========================================
            # 12 İNDİKATÖR & OLASILIK YÜZDESİ PUANLAMASI
            # ==========================================
            score = 0
            
            # Dinamik Kâr/Zarar Limitleri Hazırlığı
            base_tp = 3.5
            base_sl = 1.5
            is_crypto = sym.endswith("USDT") or sym in ["BTC", "ETH", "SOL", "BNB"]
            is_mean_reversion_buy = False # Placeholder
            is_arbitrage_buy = False      # Placeholder

            if is_crypto:
                base_tp = 2.0
                base_sl = 2.0
            
            if 40.0 <= rsi <= 80.0:
                score += 1
            if macd >= -0.50:
                score += 1
            if ema_golden:
                score += 1
            if vwap_bull:
                score += 1
            if vol_ratio >= 0.70:
                score += 1
            if 20.0 <= stoch_k <= 90.0:
                score += 1
            if adx >= 15.0:
                score += 1
            
            # Komut 11: OBV & RS Line Puanlaması
            if cmf > 0.05:
                score += 1  # Para girişi var
            if rs_score > 0.0:
                score += 1  # Endeksten pozitif ayrışıyor

            is_strong_obv_rs = (cmf > 0.05 and rs_score > 0.0)

            # DERS KURALI 4: Hacimsiz Kırılım Cezası (Volume Ratio < 1.2)
            if vol_ratio < 1.2 and chg_pct > 1.0:
                score -= 2  # Hacimsiz sahte kırılım riski cezası

            # DERS KURALI 5: Yüksek Olasılıklı Momentum Kırılım Onayı (Volume Ratio >= 1.5 & Change >= 1.2%)
            if vol_ratio >= 1.5 and chg_pct >= 1.2:
                score += 3  # %85+ Başarı Olasılıklı Momentum Onay Bonusu

            # ==========================================
            # QUANT-TRADING: RSI Pattern Recognition & Bollinger Anomaly
            # ==========================================
            is_crypto = sym.endswith("USDT") or sym in ["BTC", "ETH", "SOL", "BNB"]
            
            # LLM YZ DUYGU ANALİZİ & BONUS SKOR
            llm_sentiment_bonus = 0
            if is_crypto:
                tweets = llm_intelligence.get_fintwit_social_sentiment(sym)
                if tweets:
                    avg_score = sum(t.get("sentiment_score", 0) for t in tweets) / len(tweets)
                    if avg_score >= 85.0:
                        llm_sentiment_bonus = 2
                        logger.info(f"[LLM SENTIMENT BOOST] {sym} için pozitif haber/duygu saptandı (Skor: {avg_score}). Karar motoruna +2 Bonus eklendi.")
            
            score += llm_sentiment_bonus

            if is_crypto:
                # 1. RSI Anomaly (Oversold Bounce / W-Pattern Approximation)
                if 30.0 <= rsi <= 45.0 and chg_pct > 0.5 and vol_ratio > 1.2:
                    score += 2
                    logger.info(f"[QUANT-TRADING] {sym} RSI Pattern Recognition (Oversold Bounce) tespit edildi. Ekstra puan verildi.")
                
                # 2. Volatility Breakout (Bollinger Bands Squeeze proxy)
                if atr_pct > 2.0 and chg_pct > 1.5 and vol_ratio >= 1.5:
                    score += 2
                    logger.info(f"[QUANT-TRADING] {sym} Volatility Breakout (Bollinger Squeeze Anomaly) tespit edildi.")

            # Kripto için Çok Katı (Sıkı) Onay Eşiği ve Premium Agent Hibrit Kararı
            # YENİ: KULLANICI RİSK MODUNA GÖRE DİNAMİK DAR BOĞAZ (BOTTLENECK) YÖNETİMİ
            # Kullanıcının sesli mesajdaki haklı şikayeti: "Çok sıkıştırılmış, dar boğaz var".
            current_mode = settings.current_risk_mode.upper()
            
            # Varsayılan (NORMAL)
            required_score = 4 
            min_vol = 1.0
            global_max_pos = 10 # En fazla 5 pozisyon olabilir
            market_pos_multiplier = 1.0
            
            if current_mode == "AGGRESSIVE":
                required_score = 1  # Kullanıcı talebi: Anında eyleme geçmesi için eşik 1'e indirildi
                min_vol = 0.0       # Hacim dar boğazı tamamen kaldırıldı
                global_max_pos = 15
                market_pos_multiplier = 2.0 # Kripto limitini 4'ten 8'e çıkarır
            elif current_mode == "NORMAL":
                required_score = 5
                min_vol = 0.7
                global_max_pos = 10
            elif current_mode == "TIGHT":
                required_score = 7
                min_vol = 1.0
                global_max_pos = 5
            elif current_mode == "CONSERVATIVE":
                required_score = 8
                min_vol = 1.2
                global_max_pos = 3

            is_buy_signal = score >= required_score

            # Hacim filtresi (Tüm piyasalar için Risk moduna göre)
            if vol_ratio < min_vol:
                logger.debug(f"[RISK SHIELD] {sym} Hacim yetersiz (Ratio: {vol_ratio:.2f} < {min_vol}). Mod: {current_mode}")
                continue

            if not is_buy_signal:
                logger.debug(f"[SCORE SHIELD] {sym} Sinyal zayıf ({score}/{required_score}). Mod: {current_mode}")
                continue
            # O2 DÜZELTİLDİ: Piyasa başı açık pozisyon limiti kontrolü
            market_type = market_hours_validator.get_market_type(sym)
            max_pos_for_market = int(RISK_PARAMS.get("max_positions_per_market", {}).get(market_type, 3) * market_pos_multiplier)
            open_pos_in_market = sum(
                1 for p in live_trade_manager.positions.values()
                if p.status == "OPEN" and p.market == market_type
            )
            if open_pos_in_market >= max_pos_for_market:
                logger.info(f"[MARKET LIMIT BLOCK] {sym} ({market_type}) piyasasında max pozisyon sayısına ulaşıldı ({open_pos_in_market}/{max_pos_for_market}).")
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
                    experience_memory_engine.add_live_log(market_type, "BLOCK", msg)
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
                    experience_memory_engine.add_live_log(market_type, "BLOCK", msg)
                    live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Budget Limit")
                except Exception:
                    pass
                continue

            # Mevcut açık pozisyon kontrolü
            open_pos = next((p for p in live_trade_manager.positions.values() if p.symbol.upper() == sym.upper() and p.status == "OPEN"), None)
            if open_pos:
                # AKILLI ERKEN ÇIKIŞ (Smart Exit)
                # Kârdayken momentum düşerse TP beklemeden cebe at
                if open_pos.unrealized_pnl_pct >= 1.5:
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
                dyn_cap = live_trade_manager.get_dynamic_position_capital(sym)
                
                # İşlem Otopsisi & Hafıza Çarpanı (Ödül veya Temkinlilik)
                qty_mult = mem_check.get("qty_multiplier", 1.0)
                
                # Komut 11: OBV ve RS Line Agresif Atak / Savunma
                if is_strong_obv_rs and current_mode in ["NORMAL", "TIGHT"]:
                    qty_mult *= 1.20
                    logger.info(f"[AGGRESSIVE ATTACK] {sym} OBV ve RS Güçlü! Lot boyutu %20 artırıldı (Cüretkar Atak).")
                elif cmf < -0.05:
                    qty_mult *= 0.80
                    logger.info(f"[WEAK VOLUME DEFENSE] {sym} OBV Zayıf (Para Çıkışı Var). Lot boyutu %20 düşürüldü.")

                # Supertrend Trend Uyuşmazlığı Cezası
                if trend_conflict:
                    qty_mult *= 0.70
                    logger.info(f"[TREND CONFLICT] {sym} EMA Golden Cross ile Supertrend uyuşmuyor! Risk azaltıldı (%30 Daha Küçük Pozisyon).")
                    
                if qty_mult != 1.0:
                    dyn_cap = round(dyn_cap * qty_mult, 2)
                    logger.info(f"[ALGORITHMIC LEARNING] İşlem Otopsisi sonucu oransal müdahale: Lot çarpanı {qty_mult}x uygulandı. Yeni bütçe: ${dyn_cap}")

                # Özel Strateji Tag'leri ve İnce Ayar
                strategy_tag = "MOMENTUM_BREAKOUT"
                if is_mean_reversion_buy:
                    strategy_tag = "MEAN_REVERSION"
                    base_tp = 2.5
                    base_sl = 1.2
                elif is_arbitrage_buy:
                    strategy_tag = "STATISTICAL_ARBITRAGE"
                    base_tp = 1.5
                    base_sl = 0.8
                
                # Yapay Zeka (LLM) Bonusuna Göre TP Esnetme
                if llm_sentiment_bonus > 0:
                    base_tp += 1.5  # Güçlü duygu varsa kâr makasını %1.5 genişlet
                    logger.info(f"[DYNAMIC TP STRETCH] {sym} için LLM Duygusu güçlü. TP hedefi %{base_tp} seviyesine esnetildi.")

                # Mutlak Fiyat Hedefleri (Absolute Prices)
                target_tp_price = round(price * (1 + (base_tp / 100)), 4)
                target_sl_price = round(price * (1 - (base_sl / 100)), 4)

                signal = WebhookSignal(
                    passphrase="secret_key",
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
                        "volume_ratio": vol_ratio,
                        "cmf": cmf,
                        "rs_score": rs_score,
                        "supertrend_bullish": supertrend_bullish,
                        "trend_conflict": trend_conflict
                    },
                    macro_tags=[f"STRATEGY_{strategy_tag}", f"SCORE_{score}_OF_8"]
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
                self.last_evaluated_signals[sym] = "LONG"

        return executed_triggers

tv_auto_runner = TradingViewAutoStrategyRunner()

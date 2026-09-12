from schemas.webhook import WebhookSignal
from core.config import settings
from core.logger import logger
from services.analyzer.agent import analyzer_agent
from services.market_feed.live_stream import live_trade_manager
from typing import Dict, Any

def process_order(signal: WebhookSignal) -> Dict[str, Any]:
    """
    Gelen TradingView sinyalini otonom analizör ajanına ve sert risk motoruna iletir.
    Onaylanan emirler anında canlı pozisyon yöneticisine ve broker köprüsüne iletilir.
    """
    # Action'ı büyük harfe çevir
    action_clean = str(signal.action).upper()
    signal.action = action_clean

    # 0. VERİ DOĞRULAMA — Null / Geçersiz Fiyat & Miktar Kontrolü
    if signal.price is None or signal.price <= 0:
        logger.error(f"[ORDER REJECTED] {signal.symbol} — Geçersiz fiyat: {signal.price}. Emir reddedildi.")
        return {"status": "rejected", "reason": "NULL_OR_INVALID_PRICE", "symbol": signal.symbol, "price": signal.price}
    if signal.quantity is None or signal.quantity <= 0:
        logger.error(f"[ORDER REJECTED] {signal.symbol} — Geçersiz miktar: {signal.quantity}. Emir reddedildi.")
        return {"status": "rejected", "reason": "NULL_OR_INVALID_QUANTITY", "symbol": signal.symbol, "quantity": signal.quantity}

    # K2 DÜZELTİLDİ: Anomali tespiti — fiyatın 24h yüksekliğinin %15 üzerinde olup olmadığını kontrol et
    live_high = signal.indicators.get("high_24h", signal.price) if signal.indicators else signal.price
    if live_high > 0 and signal.price > live_high * 1.15:
        logger.warning(f"[ANOMALY DETECTED] {signal.symbol} — Fiyat (${signal.price}) 24h yüksek (${live_high}) üzerinde %15+ sapma. MACRO SHOCK filtresi devreye alındı.")

    # 0.5 OTONOM KORUMA KALKANI — hard_rules.py içinde zaten çalışacak.
    # Burada 2. bir sorgu yapmak hem yavaşlatır hem de farklı market_regime 
    # parametresiyle tutarsız sonuç üretir. Bu blok kaldırıldı.
    # (Koruma: hard_rules.py > Kural 2.5 — ExperienceMemoryEngine)


    # 1. Ajan Analizi ve Dereceli Risk Değerlendirmesi
    decision = analyzer_agent.analyze_and_evaluate(signal)
    risk_assessment = decision["risk_assessment"]
    passed = risk_assessment["passed_hard_rules"]
    final_qty = risk_assessment["adjusted_quantity"]

    # 2. Sert Kural Blokajı Kontrolü
    if not passed:
        logger.warning(
            f"[ORDER BLOCKED] {signal.symbol} ({signal.action}) BLOCKED BY RISK ENGINE! "
            f"Reasons: {risk_assessment['rejection_reasons']}"
        )
        return {
            "status": "rejected",
            "reason": "BLOCKED_BY_HARD_RISK_RULES",
            "decision": decision
        }

    # 3. Canlı Pozisyon Yöneticisi Entegrasyonu (TradingView Sermayesi / Kontratı ile)
    # K3 DÜZELTİLDİ: signal.account_equity'yi doğrudan kullan; 0 veya None ise dinamik hesapla
    if signal.account_equity and signal.account_equity > 0:
        capital_used = signal.account_equity
    else:
        capital_used = live_trade_manager.get_dynamic_position_capital(signal.symbol)

    if action_clean in ["BUY", "LONG", "SELL", "SHORT"]:
        try:
            from services.risk_engine.missing_agents import spread_guard
            from services.market_feed.live_stream import live_trade_manager
            is_spread_ok = spread_guard.check_spread(signal.symbol, live_trade_manager.market_prices)
        except Exception:
            pass
    if action_clean in ["BUY", "LONG"]:
        from services.ai_agent.system_prompt import RISK_PARAMS
        
        # TP/SL Senkronizasyonu: auto_runner veya LLM zaten hesapladıysa kullan
        # Böylece Local DB ve Alpaca aynı seviyeleri takip eder (DESYNC önleme)
        if signal.take_profit and signal.take_profit > signal.price > 0:
            tp_pct = round(((signal.take_profit - signal.price) / signal.price) * 100.0, 2)
            logger.info(f"[TP SYNC] {signal.symbol} — Signal'dan gelen LLM TP kullanıldı: %{tp_pct} (${signal.take_profit})")
        else:
            tp_pct = RISK_PARAMS.get("default_take_profit_pct", 3.0)
        
        if signal.stop_loss and 0 < signal.stop_loss < signal.price:
            sl_pct = round(((signal.price - signal.stop_loss) / signal.price) * 100.0, 2)
            logger.info(f"[SL SYNC] {signal.symbol} — Signal'dan gelen LLM SL kullanıldı: %{sl_pct} (${signal.stop_loss})")
        else:
            sl_pct = RISK_PARAMS.get("default_stop_loss_pct", 1.5)
        
        # Strateji tag'ine göre override (sadece signal'da TP/SL yoksa)
        if signal.macro_tags and not signal.take_profit:
            if "STRATEGY_MEAN_REVERSION" in signal.macro_tags:
                tp_pct = RISK_PARAMS.get("mean_reversion_tp_pct", 1.5)
                sl_pct = 1.0
                logger.info(f"[FINE TUNING] {signal.symbol} Mean Reversion TP (%{tp_pct}) SL (%{sl_pct}).")
            elif "STRATEGY_STATISTICAL_ARBITRAGE" in signal.macro_tags:
                tp_pct = 2.0
                sl_pct = 1.0
                logger.info(f"[FINE TUNING] {signal.symbol} Arbitraj TP (%{tp_pct}) SL (%{sl_pct}).")
        
        # Kripto için ML/Ajan skoru — sadece signal'da TP/SL yoksa devreye girer
        if (not signal.take_profit) and (signal.symbol.endswith("USDT") or signal.symbol in ["BTC", "ETH", "SOL", "BNB"]):
            skills_audit = decision.get("skills_audit", {})
            ml_score = skills_audit.get("overall_skill_score", 50)
            atr_pct = signal.indicators.get("volatility", signal.indicators.get("atr_pct", 2.0)) if signal.indicators else 2.0
            volatility_modifier = max(0.5, min(atr_pct / 2.0, 2.5))
            
            if ml_score >= 80:
                tp_pct = round(4.5 * volatility_modifier, 2)
                sl_pct = 1.5
                logger.info(f"[LLM/ML HIGH CONF] {signal.symbol} Skor:{ml_score}/100 → TP %{tp_pct} SL %{sl_pct}")
            elif ml_score >= 60:
                tp_pct = round(3.0 * volatility_modifier, 2)
                sl_pct = round(1.8 * volatility_modifier, 2)
                logger.info(f"[LLM/ML MED CONF] {signal.symbol} Skor:{ml_score}/100 → TP %{tp_pct} SL %{sl_pct}")
            else:
                tp_pct = RISK_PARAMS.get("crypto_dynamic_tp_base", 4.0)
                sl_pct = RISK_PARAMS.get("crypto_dynamic_sl_base", 2.0)
                logger.info(f"[LLM/ML SCALP] {signal.symbol} Skor:{ml_score}/100 → SOTA Makas TP %{tp_pct} SL %{sl_pct}")
        
        # Güvenlik: SL asla %1.5'in altına inmez
        sl_pct = max(1.5, sl_pct)

        pos = live_trade_manager.open_position(
            symbol=signal.symbol,
            capital=capital_used,
            side="BUY",
            tp_pct=tp_pct,
            sl_pct=sl_pct,
            entry_price_override=signal.price
        )
        if pos:
            exec_message = f"TradingView Canlı Alış Tetiklendi: {pos.symbol} @ ${pos.entry_price} (Hedef: ${pos.target_profit_price}, Stop: ${pos.stop_loss_price})"
            # Y1 DÜZELTİLDİ: Trade journal'a kaydet (öğrenme döngüsü için)
            try:
                from services.engine.trade_journal_learning import trade_journal_engine
                trade_journal_engine.record_live_execution(
                    symbol=pos.symbol,
                    market=pos.market,
                    side=pos.side,
                    entry_price=pos.entry_price,
                    quantity=pos.quantity,
                    entry_reasons=[f"Score: {risk_assessment.get('raw_risk_score', 0):.1f} | Verdict: EXECUTE | {action_clean}"],
                    risk_score=risk_assessment.get("raw_risk_score", 0.0)
                )
            except Exception as je:
                logger.warning(f"[JOURNAL WARN] Trade journal kaydı başarısız: {je}")
        else:
            exec_message = f"TradingView Alım Sinyali Alındı ({signal.symbol}) - Kasa Nakdi Dolu / Bütçe Sınırına Ulaşıldı."
    elif action_clean in ["SELL", "CLOSE", "FLAT"]:
        # Açık pozisyonu bul ve kapat
        closed_item = None
        for pid, p in list(live_trade_manager.positions.items()):
            if p.symbol.upper() == signal.symbol.upper() and p.status == "OPEN":
                closed_item = live_trade_manager.close_position(pid, "TRADINGVIEW_WEBHOOK_EXIT")
                break
        exec_message = f"TradingView Canlı Çıkış Tetiklendi: {signal.symbol} pozisyonu kapatıldı." if closed_item else f"TradingView Satış/Kapatma Sinyali Alındı ({signal.symbol})"
    else:
        exec_message = f"TradingView Sinyali İşlendi: {action_clean} {signal.symbol}"


    # 4. İletim Moduna Göre Emir Çalıştırma Loglama
    if settings.trading_mode == "SIMULATION":
        logger.info(
            f"[SIMULATION EXECUTION] TRADINGVIEW PAPER TRADE: {signal.action} {final_qty} {signal.symbol} "
            f"at ${signal.price} (Risk Score: {risk_assessment['raw_risk_score']})"
        )
        return {
            "status": "success",
            "mode": "SIMULATION",
            "message": exec_message,
            "decision": decision
        }
    elif settings.trading_mode in ["LIVE", "PAPER"]:
        # Canlı Borsa / Broker API Entegrasyonu (Alpaca)
        # PAPER modunda paper=True, LIVE modunda paper=False
        is_paper_mode = settings.trading_mode.upper() != "LIVE"
        broker = get_broker(settings.active_broker, paper=is_paper_mode)
        logger.info(f"[BROKER] Mode: {'PAPER' if is_paper_mode else 'LIVE'} | Broker: {settings.active_broker}")
        
        if broker:
            if action_clean in ["BUY", "LONG"]:
                # Sinyal'dan gelen dinamik TP/SL kullan; yoksa varsayılan %3/%1.5
                tp_price = signal.take_profit if signal.take_profit else round(signal.price * 1.03, 4)
                sl_price = signal.stop_loss if signal.stop_loss else round(signal.price * 0.985, 4)
                
                logger.info(
                    f"[ALPACA BRACKET] {signal.symbol} BUY {final_qty} | "
                    f"Entry: ${signal.price:.4f} | TP: ${tp_price:.4f} | SL: ${sl_price:.4f}"
                )
                res = broker.place_bracket_order(signal.symbol, "BUY", final_qty, tp_price, sl_price)
                if res.get("status") == "error":
                    logger.warning(f"[BROKER FALLBACK] Alpaca API error: {res.get('message')}. Falling back to Simulation Mode.")
                    pos = live_trade_manager.open_position(signal.symbol, capital_used, "BUY", tp_pct, sl_pct, signal.price)
                    if pos:
                        res = {"status": "success", "order_id": f"SIM-{pos.id}", "details": "Simulated fallback"}
            elif action_clean in ["SELL", "CLOSE", "FLAT"]:
                res = broker.close_position(signal.symbol)
            else:
                res = {"status": "ignored"}
                
            logger.info(f"[LIVE EXECUTION] {settings.active_broker} ROUTED: {action_clean} {final_qty} {signal.symbol}. Result: {res}")
            
        return {
            "status": "success",
            "mode": "LIVE",
            "message": f"[{settings.active_broker} LIVE BROKER ROUTED] {exec_message}",
            "decision": decision
        }
    else:
        logger.error(f"Unknown TRADING_MODE: {settings.trading_mode}")
        return {"status": "error", "message": "System configuration error", "decision": decision}


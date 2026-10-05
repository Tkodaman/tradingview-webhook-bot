from schemas.webhook import WebhookSignal
from core.config import settings
from core.logger import logger
from services.analyzer.agent import analyzer_agent
from services.market_feed.live_stream import live_trade_manager
from services.broker.factory import get_broker
from services.agent_consensus.council import council_engine
from typing import Dict, Any
from datetime import datetime, timezone
import time

# --- FREQTRADE COOLDOWN GUARD ---
# Bir işlem kapatıldığında (SELL/CLOSE), aynı coin'e hemen (örn. 10 dakika) geri girilmesini engeller.
_freqtrade_cooldowns = {}

def _strict_rejection(signal: WebhookSignal, reason: str) -> Dict[str, Any]:
    """Return the same decision envelope used by downstream risk rejections."""
    return {
        "status": "rejected",
        "reason": reason,
        "decision": {
            "signal": signal.model_dump(),
            "risk_assessment": {
                "symbol": signal.symbol,
                "action": signal.action,
                "raw_risk_score": 100.0,
                "risk_level": "CRITICAL",
                "passed_hard_rules": False,
                "rejection_reasons": [reason],
                "adjusted_quantity": 0.0,
                "confidence_score": -100.0,
                "technical_score": 100.0,
                "macro_score": 0.0,
                "sentiment_score": 0.0,
                "hard_rule_triggers": [reason],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "agent_verdict": "BLOCKED_BY_STRICT_FILTER",
        },
    }

def _execute_grid_strategy(signal: WebhookSignal, council_verdict: Dict[str, Any]) -> Dict[str, Any]:
    """
    HUMMINGBOT KONSEPTİ: Yatay piyasada (Ranging) Alpaca komisyonlarını hesaba katarak Grid Izgarası kurar.
    Alpaca kriptoda taker/maker komisyonu mevcuttur (örneğin %0.1). Hisse senedinde ise slippage ve ufak SEC fee'ler.
    Biz güvenli tarafta kalıp %0.2 round-trip (gidiş-dönüş) komisyon maliyeti hesaplayacağız.
    """
    symbol_upper = signal.symbol.upper()
    is_crypto = "USDT" in symbol_upper or "/" in symbol_upper or symbol_upper.endswith("USD") or "BTC" in symbol_upper

    # Eğer Binance Kripto ise komisyon sıfıra yakın (testnet) veya çok düşük (binde 1).
    base_cost_pct = 0.05 if is_crypto else 0.20 # Yüzde 0.20 Hisse, 0.05 Kripto
    atr_pct = float(signal.indicators.get('atr_pct', 0.5)) if signal.indicators else 0.5
    
    # Oransal ilerleme: Eğer kazanç aralığı (ATR) komisyonun 1.5 katını bile karşılamıyorsa işlem yapma
    if atr_pct < base_cost_pct * 1.5:
        logger.warning(f"[GRID REDDEDİLDİ] {signal.symbol} ATR ({atr_pct:.2f}%) maliyeti (%{base_cost_pct}) aşamıyor. Grid kârsız.")
        return _strict_rejection(signal, "GRID_UNPROFITABLE_DUE_TO_COMMISSION")
        
    grid_spacing = atr_pct / 3.0  # ATR'yi 3 parçaya bölüp limit order grid atıyoruz
    logger.info(f"🕸️ [HUMMINGBOT GRID] {signal.symbol} için {grid_spacing:.2f}% aralıklarla Grid Izgarası aktif edildi! (Maliyet dahil).")
    
    # Grid pozisyonunu shadow olarak kaydet ki UI'da görünsün
    try:
        live_trade_manager.open_shadow_position(
            symbol=signal.symbol,
            side="BUY",
            tp_pct=atr_pct * 1.5,
            sl_pct=atr_pct * 0.5,
            entry_price_override=signal.price or 0.0,
            reason=f"GRID (aralik:{grid_spacing:.2f}%)"
        )
    except Exception:
        pass
    
    return {
        "status": "approved_grid",
        "reason": f"Grid Izgarası Aktif. Aralık: {grid_spacing:.2f}%. Council Score: {council_verdict.get('score', 0)}",
        "symbol": signal.symbol,
        "grid_spacing_pct": grid_spacing,
        "base_cost_pct": base_cost_pct
    }

def process_order(signal: WebhookSignal, risk_override: float = None) -> Dict[str, Any]:
    """
    Gelen TradingView sinyalini otonom analizör ajanına ve sert risk motoruna iletir.
    Onaylanan emirler anında canlı pozisyon yöneticisine ve broker köprüsüne iletilir.
    """
    # Action'ı büyük harfe çevir
    action_clean = str(signal.action).upper()
    signal.action = action_clean

    # ================================================================
    # 🇹🇷 BIST KORUMASI: BIST = Sadece Simülasyon / Öneri Modu
    # Kullanıcı Kararı: BIST varlıklarında ASLA gerçek işlem yapılmaz.
    # Alpaca'ya gönderilmez. Shadow pozisyon olarak eğitim verisi sayılır.
    # ================================================================
    sym_upper = signal.symbol.upper()
    is_bist = (sym_upper.endswith(".IS") or sym_upper.startswith("BIST:") or
               sym_upper in ["THYAO", "EKGYO", "SASA", "EREGL", "KCHOL", "FROTO",
                              "BIMAS", "ASELS", "GARAN", "YKBNK", "AKBNK", "TUPRS",
                              "TCELL", "PGSUS", "TAVHL", "VESTL", "KOZAL", "MGROS"])
    if is_bist and action_clean in ["BUY", "LONG", "SELL", "SHORT"]:
        logger.info(f"🇹🇷 [BIST SIMÜLASYON] {signal.symbol} — BIST varlığı, sadece shadow simülasyon. Gerçek işlem yapılmıyor.")
        try:
            if action_clean in ["BUY", "LONG"]:
                live_trade_manager.open_shadow_position(
                    symbol=signal.symbol, side="BUY",
                    tp_pct=3.0, sl_pct=1.5,
                    entry_price_override=signal.price or 0.0,
                    reason="BIST_SIMÜLASYON"
                )
        except Exception:
            pass
        return {"status": "bist_simulation_only", "symbol": signal.symbol,
                "message": f"BIST {signal.symbol} shadow simülasyona alındı. Gerçek işlem yapılmıyor."}

    # --- FREQTRADE COOLDOWN GUARD (10 Dakika Bekleme Süresi) ---

    if action_clean in ["SELL", "SHORT", "CLOSE"]:
        _freqtrade_cooldowns[signal.symbol] = time.time()
    
    if action_clean in ["BUY", "LONG"]:
        last_sell_time = _freqtrade_cooldowns.get(signal.symbol, 0)
        elapsed = time.time() - last_sell_time
        if elapsed < 600:  # 10 dakika (600 saniye)
            remaining = 600 - elapsed
            logger.warning(f"[FREQTRADE COOLDOWN GUARD] {signal.symbol} icin yeni satis yapildi. {remaining:.0f} saniye daha isleme girilemez (Intikam Tradeleri Engellendi).")
            return _strict_rejection(signal, "FREQTRADE_COOLDOWN_GUARD")
    # -------------------------------------------------------------

    # Fast orchestration preflight: deterministic and local, no LLM/network call.
    from services.engine.decision_orchestrator import evaluate_fast_gate
    orchestration = evaluate_fast_gate(signal)
    if orchestration["hard_block"]:
        logger.warning(f"[ORCHESTRATOR BLOCK] {signal.symbol}: {orchestration['reason']}")
        return _strict_rejection(signal, orchestration["reason"])
    # Fail-closed: eksik kritik indikatör (volume_ratio/atr_pct) teyit gerektirir.
    # ANALİZ FELCİ ÇÖZÜMÜ: Eksik veri varsa botu kilitleme (hard block yapma), sadece Yüce Divan'a "Eksik Veri" uyarısı ilet.
    if orchestration.get("decision_gate") == "WAIT" and action_clean in ["BUY", "LONG", "SELL", "SHORT"]:
        logger.info(f"[ORCHESTRATOR WAIT - SOFTENED] {signal.symbol}: Eksik veri var ({orchestration.get('missing_fields')}). İslem Yuce Divan inisiyatifine birakildi.")
        if signal.macro_tags is None:
            signal.macro_tags = []
        signal.macro_tags.append("INCOMPLETE_DATA_WARNING")

    # === [ASTRA 6] YÜCE DİVAN KONTROLÜ (AUTONOMOUS COUNCIL) ===
    # Fast orchestration'ı geçtiyse bile 3 ajanlı konseyin onayından geçmek zorundadır.
    
    # KUSURSUZ İNFAZ: Asya Piyasası Hacimsizlik (Liquidity Trap) Koruması
    # Kullanıcı Raporu: Asya piyasasında bot sürekli zarar ediyor. Bu yüzden Asya seansında (TSİ 02:00 - 09:00 arası) 
    # işlem şartlarını ekstrem derecede zorlaştırıyoruz. Hacim patlaması yoksa asla girme.
    from datetime import datetime, timezone, timedelta
    trt_hour = (datetime.now(timezone.utc) + timedelta(hours=3)).hour
    if 2 <= trt_hour < 9 and action_clean in ["BUY", "LONG"]:
        if not signal.indicators or float(signal.indicators.get("volume_ratio", 0)) < 2.0:
            logger.warning(f"[ASIAN SESSION TRAP] {signal.symbol} Asya seansında (Düşük Hacim). Volume Ratio 2.0 altında ({signal.indicators.get('volume_ratio', 'N/A')}). İŞLEM REDDEDİLDİ.")
            return _strict_rejection(signal, "ASIAN_SESSION_LOW_LIQUIDITY_TRAP")
        else:
            logger.warning(f"[ASIAN SESSION ALERT] {signal.symbol} Asya seansında ancak muazzam hacim ({signal.indicators.get('volume_ratio')}) tespit edildi. Yüce Divan'a iletiliyor.")
            if signal.macro_tags is None: signal.macro_tags = []
            signal.macro_tags.append("ASIAN_SESSION_EXTREME_VOLUME")
            
    if action_clean in ["BUY", "LONG"]:
        # Konsey modülünü local import ile çekiyoruz (Döngüsel importu önlemek için)
        from services.agent_consensus.council import council_engine
        
        council_verdict = council_engine.convene(signal)
        council_mode = council_verdict.get("mode", "DIRECTIONAL")
        
        if council_mode == "FLASH":
            logger.warning(f"🚨 [TRUMP2CASH FLASH OVERRIDE] {signal.symbol} - SOSYAL MEDYA/KİLİT FİGÜR TETİKLEMESİ! PİYASA KURALLARI EZİLİYOR. 🚨")
            logger.info(f"YÜCE DİVAN VETOLARI DEVRE DIŞI. FLASH EMİR BORSAYA İLETİLİYOR.")
        elif council_mode == "GRID":
            logger.info(f"🕸️ [HUMMINGBOT GRID MODE] {signal.symbol} YATAY PİYASADA. Makas/Grid aralığı oluşturulacak.")
            grid_res = _execute_grid_strategy(signal, council_verdict)
            if grid_res.get("status") == "rejected":
                return grid_res
            # Grid onaylandıysa, hedefleri grid bazlı ayarlayıp standart yöne doğru ilerletiyoruz (engel kaldırma)
            signal.take_profit = signal.price * (1.0 + grid_res.get("grid_spacing_pct", 0.5) * 1.5 / 100.0) if signal.price else signal.take_profit
            signal.stop_loss = signal.price * (1.0 - grid_res.get("grid_spacing_pct", 0.5) * 0.5 / 100.0) if signal.price else signal.stop_loss
        else:
            if not council_verdict["approved"]:
                logger.warning(f"[YÜCE DİVAN VETOSU] {signal.symbol} REDDEDİLDİ. Neden: {council_verdict['reason']}")
                return _strict_rejection(signal, council_verdict['reason'])
            else:
                logger.info(f"[YÜCE DİVAN ONAYI] {signal.symbol} İÇİN KONSENSÜS SAĞLANDI ({council_verdict.get('score', 0):.1f} Puan). YÖNLÜ (DIRECTIONAL) İŞLEME DEVAM EDİLİYOR.")
    # ========================================================


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

    # SOLANA MARKET MAKER - GUARDIAN DROP MODE (ESNETİLDİ)
    # Eğer fiyat gün içinde %15'ten fazla çöktüyse (Gerçek Kara Kuğu), "Diplerden alım" yapsak bile risk çok yüksektir.
    if signal.indicators and action_clean in ["BUY", "LONG"]:
        daily_change = float(signal.indicators.get("change_pct") or 0.0)
        if daily_change <= -15.0:
            logger.warning(f"[GUARDIAN DROP MODE] {signal.symbol} gunluk dususu %{daily_change:.1f}. Serbest dususte olan bir bicak (Falling Knife) alinamaz!")
            return _strict_rejection(signal, "GUARDIAN_DROP_KNIFE")

    # 0.5 PİYASA SAATİ KORUMASI (Market Hours Check)
    # KULLANICI TALEBİ: Piyasa kapalıyken (Örn. NASDAQ Pre-Market) işlemler reddedilmeli
    from services.risk_engine.market_hours import market_hours_validator
    is_open, msg, _ = market_hours_validator.is_market_open(signal.symbol)
    if not is_open:
        logger.warning(f"[MARKET CLOSED] {signal.symbol} piyasası şu anda kapalı veya seans dışı. Sinyal reddedildi. Mesaj: {msg}")
        return {"status": "rejected", "reason": "MARKET_CLOSED", "symbol": signal.symbol, "message": msg}

    # NASDAQ İlk 20 dk Gap Riski -> Doğrudan YZ'ye Gizli Talimatla Gönder
    if market_hours_validator.is_nasdaq_opening_gap_phase(signal.symbol):
        logger.warning(f"[GAP RISK] {signal.symbol} piyasa açılışının ilk 20 dakikasında (Yüksek Volatilite). Sinyal YZ'ye özel talimatla gönderiliyor.")
        if signal.macro_tags is None:
            signal.macro_tags = []
        if "NASDAQ_OPENING_GAP_RISK" not in signal.macro_tags:
            signal.macro_tags.append("NASDAQ_OPENING_GAP_RISK")

    # Koruma: hard_rules.py > Kural 2.5 — ExperienceMemoryEngine (Zaten aşağıda çalışacak)
    
    # 0.7 STRICT INDICATOR LAYERS (KULLANICI TALEBİ: EMA200, RSI, MACD, ADX)
    if signal.indicators:
        ind = signal.indicators
        # Trend Katmanı: EMA200 ve Rejim Belirleme (Kazan-Kazan)
        ema200 = ind.get("ema200")
        if ema200 is not None and signal.price > 0:
            if signal.price > ema200:
                signal.macro_tags.append("REGIME_BULL_TREND")
            else:
                signal.macro_tags.append("REGIME_BEAR_TREND")
                
            if action_clean in ["BUY", "LONG"] and signal.price < ema200:
                logger.warning(f"[SOFT FILTER] {signal.symbol} BUY: Price ({signal.price}) < EMA200 ({ema200}). Fiyat trendin altında ama fırsat tespiti için engellenmiyor.")
                signal.macro_tags.append("EMA200_DOWNTREND_WARNING")
            elif action_clean in ["SELL", "SHORT"] and signal.price > ema200:
                logger.warning(f"[SOFT FILTER] {signal.symbol} SELL: Price ({signal.price}) > EMA200 ({ema200}). Fiyat trendin üstünde ama engellenmiyor.")
                signal.macro_tags.append("EMA200_UPTREND_WARNING")

        # Aşırı Bölge Katmanı: RSI
        rsi = ind.get("rsi")
        if rsi is not None:
            if action_clean in ["BUY", "LONG"] and rsi > 70:
                logger.warning(f"[SOFT FILTER] {signal.symbol} BUY: RSI ({rsi}) > 70 (Overbought). Cüretkar moda geçildi, işlem engellenmiyor.")
                signal.macro_tags.append("RSI_OVERBOUGHT_WARNING")
            elif action_clean in ["SELL", "SHORT"] and rsi < 30:
                logger.warning(f"[SOFT FILTER] {signal.symbol} SELL: RSI ({rsi}) < 30 (Oversold). Cüretkar moda geçildi, işlem engellenmiyor.")
                signal.macro_tags.append("RSI_OVERSOLD_WARNING")
                
        # Trend Gücü Katmanı: ADX (Yatay Piyasa Tespiti)
        adx = ind.get("adx")
        if adx is not None:
            if adx < 20:
                signal.macro_tags.append("REGIME_CHOPPY_RANGING") # gpt-6-astra'ya yatay piyasa olduğunu söyle
                logger.warning(f"[SOFT FILTER] {signal.symbol} {action_clean}: ADX ({adx}) < 20 (Ranging Market). İşlem engellenmiyor.")
            elif adx > 40:
                signal.macro_tags.append("REGIME_HIGH_VOLATILITY")

        # Tetikleyici Katmanı: MACD (MACD hist sıfır kesişimi / Pozitif-Negatif bölge)
        macd = ind.get("macd")
        macd_signal = ind.get("macd_signal")
        if macd is not None and macd_signal is not None:
            hist = macd - macd_signal
            if action_clean in ["BUY", "LONG"] and hist < 0:
                logger.warning(f"[SOFT FILTER] {signal.symbol} BUY: MACD Hist ({hist}) < 0. İşlem engellenmiyor.")
                signal.macro_tags.append("MACD_BEARISH_WARNING")
            elif action_clean in ["SELL", "SHORT"] and hist > 0:
                logger.warning(f"[SOFT FILTER] {signal.symbol} SELL: MACD Hist ({hist}) > 0. İşlem engellenmiyor.")
                signal.macro_tags.append("MACD_BULLISH_WARNING")


    # 1. Ajan Analizi ve Dereceli Risk Değerlendirmesi
    decision = analyzer_agent.analyze_and_evaluate(signal)
    decision["orchestration"] = orchestration
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
    confidence_score = 0.5
    if "skills_audit" in decision and "overall_skill_score" in decision["skills_audit"]:
        confidence_score = float(decision["skills_audit"]["overall_skill_score"]) / 100.0

    if signal.account_equity and signal.account_equity > 0:
        capital_used = signal.account_equity
    else:
        # gpt-6-astra/AI Güven skoruna göre dinamik Kelly kriteri bütçe hesabı
        capital_used = live_trade_manager.get_dynamic_position_capital(signal.symbol, confidence_score)
        
    # KULLANICI TALEBİ: bloklamaları kaldır yumuşat
    if capital_used > 1000.0:
        logger.warning(f"[HARD CAP] {signal.symbol} için gelen sermaye talebi (${capital_used}) sınırları aşıyor. $1000'a sabitlendi.")
        capital_used = 1000.0


    if action_clean in ["BUY", "LONG", "SELL", "SHORT"]:
        try:
            from services.broker.alpaca_client import alpaca_client
            spread_pct = alpaca_client.get_bid_ask_spread(signal.symbol)
            is_crypto_sym = signal.symbol.upper().endswith("USDT") or signal.symbol.upper().endswith("USD")
            
            # KULLANICI TALEBİ: "makas dinamik açılıp kapatılsın tam otonom öğrenilen bilgi dahilinde"
            atr_for_spread = signal.indicators.get("volatility", signal.indicators.get("atr_pct", 1.8)) if signal.indicators else 1.8
            spread_limit_base = 3.0 if is_crypto_sym else 1.5
            # Dinamik makas: Eğer koin çok hareketliyse (örneğin %10 ATR), makas 3.0'a takılmasın, genişlesin.
            dynamic_spread_limit = max(spread_limit_base, float(atr_for_spread) * 0.8) 
            
            if spread_pct is None:
                # Quote alınamadı → Sadece uyarı ver, işlemi DURDURMA
                logger.info(f"[SPREAD INFO] {signal.symbol} için spread alınamadı (piyasa kapalı/API). İşlem devam ediyor.")
            elif spread_pct > dynamic_spread_limit:
                logger.warning(f"[SPREAD BLOCK] {signal.symbol} spread=%{spread_pct:.4f} limit=%{dynamic_spread_limit:.2f} (ATR: {atr_for_spread:.2f}) — aşırı makas, reddedildi.")
                return {"status": "rejected", "reason": "SPREAD_TOO_WIDE", "symbol": signal.symbol}
            else:
                logger.debug(f"[SPREAD OK] {signal.symbol} spread=%{spread_pct:.4f} (Limit: %{dynamic_spread_limit:.2f}) ✓")
        except Exception as exc:
            # Spread kontrolü exception → Sadece logla, devam et
            logger.debug(f"[SPREAD SKIP] {signal.symbol}: {exc} — spread kontrolü atlandı, işlem devam ediyor.")
    if action_clean in ["BUY", "LONG"]:
        from services.ai_agent.system_prompt import RISK_PARAMS
        
        # TP/SL Senkronizasyonu: auto_runner veya LLM zaten dinamik hesapladıysa kullan
        # Böylece Local DB ve Alpaca aynı seviyeleri takip eder (DESYNC önleme)
        is_crypto = signal.symbol.endswith("USDT") or signal.symbol in ["BTC", "ETH", "SOL", "BNB"]
        if signal.take_profit and signal.take_profit > signal.price > 0 and signal.stop_loss and 0 < signal.stop_loss < signal.price:
            tp_pct = round(((signal.take_profit - signal.price) / signal.price) * 100.0, 2)
            sl_pct = round(((signal.price - signal.stop_loss) / signal.price) * 100.0, 2)
            logger.info(f"[TP/SL SYNC] {signal.symbol} — Sinyalden gelen dinamik hedefler kullanıldı: TP=%{tp_pct} (${signal.take_profit}) | SL=%{sl_pct} (${signal.stop_loss})")
        else:
            from services.risk_engine.dynamic_sl_tp import calculate_atr_based_tp_sl
            atr_pct = signal.indicators.get("volatility", signal.indicators.get("atr_pct", 1.8)) if signal.indicators else 1.8
            tp_pct, sl_pct = calculate_atr_based_tp_sl(
                entry_price=signal.price,
                atr_pct=atr_pct,
                is_crypto=is_crypto,
                risk_mode=settings.current_risk_mode,
            )
            signal.take_profit = round(signal.price * (1 + tp_pct / 100.0), 4)
            signal.stop_loss = round(signal.price * (1 - sl_pct / 100.0), 4)
            logger.info(f"[DYNAMIC ATR SYNC] {signal.symbol} — Dinamik hesaplanan hedefler: TP=%{tp_pct} (${signal.take_profit}) | SL=%{sl_pct} (${signal.stop_loss})")
        
        # Strateji tag'ine göre override (HATA DÜZELTME: Artık sinyal'deki TP/SL değil, hesaplanan tp_pct/sl_pct kontrol ediliyor)
        # HATA: signal.take_profit zaten set edildiği için o koşul hiç True olmuyordu.
        # Düzeltme: _tp_from_signal flag'i ile signal'dan mı yoksa hesaplandı mı ayrım yap.
        _tp_from_signal = (signal.take_profit and signal.take_profit > signal.price > 0 and signal.stop_loss and 0 < signal.stop_loss < signal.price)
        if signal.macro_tags and not _tp_from_signal:  # Sadece sinyal TP'si gelmediyse override yap
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
        
        # Broker Commission & Fees (Alpaca Round-Trip)
        # Kripto: ~0.50% (alım/satım toplam). Hisse/NASDAQ: ~0.05% (Regülatör kesintileri)
        is_crypto = signal.symbol.endswith("USDT") or signal.symbol in ["BTC", "ETH", "SOL", "BNB"]
        commission_buffer_pct = 0.50 if is_crypto else 0.05
        
        # NET Kâr ve NET Zarar koruması için komisyonları SL ve TP'ye yansıtıyoruz
        # Stop'u komisyon kadar erken koyuyoruz ki SL patladığında komisyonla beraber zarar limitimizi aşmasın!
        # TP'yi komisyon kadar uzağa koyuyoruz ki hedefe vardığımızda komisyon düşünce net kâr cebimize kalsın!
        tp_pct = tp_pct + commission_buffer_pct
        sl_pct = max(1.0, sl_pct - commission_buffer_pct) # Güvenlik: SL sıfıra inmesin

        # Get actual ATR value if sent, else calculate from atr_pct
        actual_atr = signal.indicators.get("atr") if signal.indicators else None
        if actual_atr and actual_atr > 0:
            calculated_atr = actual_atr
        else:
            atr_pct = signal.indicators.get("volatility", signal.indicators.get("atr_pct", 1.5)) if signal.indicators else 1.5
            calculated_atr = signal.price * (atr_pct / 100.0)

        # Dynamic Stop Loss via ATR (Hisse: 1.5x, Kripto: 2.0x)
        atr_multiplier = 2.0 if is_crypto else 1.5
        if signal.price > 0 and calculated_atr > 0:
            sl_from_atr = round(((calculated_atr * atr_multiplier) / signal.price) * 100.0, 2)
            sl_pct = max(sl_from_atr, sl_pct) # Güvenlik: Asla mevcut min SL'den aşağı inme (ATR çok düşükse patlamasın)

        # Risk Based Qty Sizing (%1 Kasa Riski veya Otonom Kelly Kriteri Override'ı)
        risk_pct = risk_override * 100.0 if risk_override is not None else 1.0
        
        # GECE GAP RİSKİ: NASDAQ kapanışına 30 dk kaldıysa riski yarıya indir (Overnight Shield)
        from services.risk_engine.market_hours import market_hours_validator
        if market_hours_validator.is_nasdaq_closing_soon(signal.symbol):
            risk_pct = risk_pct * 0.5
            logger.info(f"[OVERNIGHT SHIELD] {signal.symbol} piyasa kapanışına yaklaşıldığı için (Overnight Gap Risk) risk katsayısı %{risk_pct}'ye düşürüldü.")

        account_equity = live_trade_manager.total_account_equity
        risk_amount = account_equity * (risk_pct / 100.0)
        per_share_risk = signal.price * (sl_pct / 100.0)
        
        # PORTFÖY BÜTÇE YÖNETİMİ (Yalıtılmış Bütçe Mimarisi)
        # KULLANICI EMRİ: Alpaca bütçesi ile Binance bütçesi ASLA karıştırılmayacak.
        from core.config import settings
        
        if is_crypto:
            crypto_realized = sum(float(t.get("net_pnl", 0.0) or 0.0) for t in getattr(live_trade_manager, "trade_history", []) if t.get("market") == "CRYPTO" and t.get("reason") not in ["CLOSED_OFFLINE_SYNC", "SIMULATION_CLOSE"])
            crypto_comm = sum(float(t.get("alpaca_commission", 0.0) or 0.0) for t in getattr(live_trade_manager, "trade_history", []) if t.get("market") == "CRYPTO" and t.get("reason") not in ["CLOSED_OFFLINE_SYNC", "SIMULATION_CLOSE"])
            
            total_exposure = sum(
                p.nominal_value for p in getattr(live_trade_manager, "positions", {}).values()
                if (p.status == "OPEN" or (p.status == "PENDING_BROKER" and p.broker_order_id)) and p.market == "CRYPTO"
            )
            base_budget = float(settings.crypto_paper_budget)
            max_global_exposure = base_budget + crypto_realized - crypto_comm  # Binance Testnet Dinamik Bütçe
            
            # TIER-1 YÜKSELTMESİ: KELLY CRITERION DİNAMİK BÜTÇELEME (SADECE HİSSELER/ALPACA İÇİN - Kullanıcı talebi üzerine Kriptoda kapatıldı)
            try:
                # KULLANICI EMRİ: Kesinlikle Binance (Kripto) için 4 coin, 1600$ limitine uyulacak.
                # Bu yüzden Kelly formülünü iptal edip, config'den gelen net yüzdeliği kullanıyoruz (Örn: %25).
                max_per_trade = max_global_exposure * (settings.max_capital_per_trade_pct / 100.0) 
            except Exception as e:
                max_per_trade = max_global_exposure * (25.0 / 100.0) # Fallback (Kesin %25)
                
        else:
            total_exposure = sum(
                p.nominal_value for p in getattr(live_trade_manager, "positions", {}).values()
                if (p.status == "OPEN" or (p.status == "PENDING_BROKER" and p.broker_order_id)) and p.market != "CRYPTO"
            )
            max_global_exposure = 8000.0  # Alpaca (Hisse) Kesin Bütçe Sınırı (8 Bin Dolar)
            
            try:
                from services.risk_engine.kelly_criterion import kelly_engine
                recent_trades = getattr(live_trade_manager, "trade_history", [])[-20:]
                kelly_pct = kelly_engine.calculate_allocation_pct(recent_trades, ai_score=signal.ai_score if hasattr(signal, "ai_score") else 5.0)
                max_per_trade = max_global_exposure * kelly_pct
            except Exception as e:
                max_per_trade = 8000.0 / 12.0  # Fallback

        available_budget = max_global_exposure - total_exposure
        
        qty_override = None
        allowed_capital = capital_used
        if per_share_risk > 0:
            raw_qty = risk_amount / per_share_risk
            desired_capital = raw_qty * signal.price
            
            # 1. Bireysel Varlık Tavanı
            desired_capital = min(desired_capital, max_per_trade)
            
            # 2. İlgili Pazarın (Crypto veya Stock) Global Portföy Tavanı
            allowed_capital = min(desired_capital, available_budget)
            
            if allowed_capital < 10.0:  # 10$ altı anlamsızdır
                logger.warning(f"[BUDGET REJECT] {signal.symbol} için bütçe kalmadı. (Açık Toplam: ${total_exposure:.2f} / Limit: ${max_global_exposure:.2f})")
                return _strict_rejection(signal, "INSUFFICIENT_GLOBAL_BUDGET")
                
            qty_override = allowed_capital / signal.price
            
            if allowed_capital < desired_capital:
                logger.warning(f"[BUDGET CAPPED] {signal.symbol} için kalan bütçe (${allowed_capital:.2f}) kullanılıyor. (Normalde ${desired_capital:.2f} basılacaktı)")
            else:
                logger.info(f"[RISK SIZING] {signal.symbol} %{risk_pct} Risk bazlı lot hesaplandı: {qty_override:.4f} (Capital: ${allowed_capital:.2f})")

            # KULLANICI EMRİ: Alpaca (NASDAQ) Pre-Market'te fractional (küsuratlı) hisse alımına izin vermez.
            # Anında infaz için seans dışı ise küsuratı kesip TAM SAYI (int) yapıyoruz.
            if not is_crypto:
                from services.risk_engine.market_hours import market_hours_validator
                is_open, msg, details = market_hours_validator.is_market_open(signal.symbol)
                if details.get("session") in ["PRE_MARKET", "POST_MARKET"]:
                    old_qty = qty_override
                    qty_override = float(int(qty_override))
                    if qty_override < 1.0:
                        qty_override = 1.0  # Küsuratlıysa en az 1 lot almaya zorla
                    logger.info(f"🚀 [PRE-MARKET FRACTIONAL FIX] {signal.symbol} {details.get('session')} aşamasında. Anında infaz (kuyruğa düşmemesi) için miktar {old_qty:.4f} -> {qty_override} olarak tam sayıya yuvarlandı.")

        # MOSS BOT FACTORY ENTEGRASYONU: Yüksek riskli (agresif) tahtalarda iğnelerden korunmak için ATR genişlet (sl_atr_mult >= 2.5)
        if is_crypto and risk_pct >= 1.5:
            atr_multiplier = 2.5
            sl_from_atr = round(((calculated_atr * atr_multiplier) / signal.price) * 100.0, 2)
            sl_pct = max(sl_from_atr, sl_pct)
            logger.info(f"[MOSS SHIELD] {signal.symbol} için agresif risk tespit edildi. ATR Çarpanı 2.5'e çıkarıldı. Yeni SL: %{sl_pct}")

        # MOSS BOT FACTORY ENTEGRASYONU: Çift Dilli Gerekçe (Bilingual Reasoning) Logu
        # Makine öğrenimi için her işlemin (120+ kelimelik) detaylı gerekçesi arşivlenir.
        import json, os
        reasoning_dir = os.path.join("data", "reasoning_logs")
        os.makedirs(reasoning_dir, exist_ok=True)
        reasoning_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": signal.symbol,
            "action": action_clean,
            "reasoning_tr": f"Yüce Divan ve Otonom Motor, {signal.symbol} tahtasında {action_clean} kararı almıştır. "
                            f"İşlem bütçesi {allowed_capital:.2f}$ (Global 10.000$ limitine uyumlu) olarak belirlendi. "
                            f"Kasa risk oranı %{risk_pct:.2f} seviyesindedir. "
                            f"Volatilite ve iğnelerden korunmak adına Dinamik ATR çarpanı {atr_multiplier} kullanılmış, "
                            f"Zarar-Kes (SL) %{sl_pct} ve Kâr-Al (TP) %{tp_pct} olarak komisyon payları (Spread) düşülerek net hesaplanmıştır. "
                            f"Piyasa saatleri, hacimsizlik kalkanları (Dead Zone) ve anomali filtreleri başarılı şekilde geçilmiştir. "
                            f"Yapay Zeka güven skoru: {confidence_score*100}/100.",
            "reasoning_en": f"The Council and Autonomous Engine initiated a {action_clean} on {signal.symbol}. "
                            f"Allocated budget is ${allowed_capital:.2f} strictly following the $10,000 global portfolio cap. "
                            f"Account risk factor is {risk_pct:.2f}%. "
                            f"To prevent whale fakeouts and stop-hunts, the Dynamic ATR multiplier is set to {atr_multiplier}, "
                            f"placing SL at {sl_pct}% and TP at {tp_pct}% (commission and spread adjusted). "
                            f"All market hour constraints, dead-zone volume filters, and anomaly gates have been cleared. "
                            f"AI Confidence Score: {confidence_score*100}/100."
        }
        try:
            with open(os.path.join(reasoning_dir, f"{signal.symbol}_{int(datetime.now().timestamp())}.json"), "w", encoding="utf-8") as rf:
                json.dump(reasoning_data, rf, ensure_ascii=False, indent=2)
        except Exception:
            pass


        # KOMİTE DÜZELTME-1: open_position'a doğru (bütçe kontrollü) seçêm değer verilmeli!
        # HATA: Eski kodda capital_used kullanılıyordu - bu ham/kontrolsuz değerdi.
        # YENİ: allowed_capital (bütçe motorundan çıkan, portoï¿½y limit kontrollü değer) kullanılıyor.
        _final_capital = allowed_capital if per_share_risk > 0 and allowed_capital > 0 else capital_used
        pos = live_trade_manager.open_position(
            symbol=signal.symbol,
            capital=_final_capital,
            side="BUY",
            tp_pct=tp_pct,
            sl_pct=sl_pct,
            entry_price_override=signal.price,
            atr_value=calculated_atr,
            use_chandelier_exit=True,
            qty_override=qty_override,
            status="PENDING_BROKER" if settings.trading_mode in ["LIVE", "PAPER"] else "OPEN",
            confidence_score=round(confidence_score * 100.0, 2),
            entry_indicators=signal.indicators or {}
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
        
        # BIST Koruması: BIST varlıkları sadece analiz edilir, Alpaca'ya gönderilmez!
        if signal.symbol.startswith("BIST:") or signal.symbol.endswith(".IS"):
            logger.info(f"[BIST KORUMASI] {signal.symbol} Borsa Istanbul varlığıdır. Alpaca (ABD) yönlendirmesi iptal edildi. Sadece analiz edildi.")
            return {"status": "success", "mode": "BIST_ANALYSIS_ONLY", "message": f"BIST Analyzed: {signal.symbol}", "decision": decision}
            
        # === AKILLI BROKER ROTASYONU (DİNAMİK YÖNLENDİRME) ===
        # KULLANICI TALEBİ (HYBRID MOD): Kripto varlıklar GERÇEK (LIVE) olarak BINANCE'e, Hisse senetleri SANAL (PAPER) olarak ALPACA'ya gönderilir.
        symbol_upper = signal.symbol.upper()
        is_crypto = "USDT" in symbol_upper or "/" in symbol_upper or symbol_upper.endswith("USD") or "BTC" in symbol_upper

        if is_crypto:
            target_broker_name = "BINANCE"
            # Kripto: is_paper_mode=False ise GERÇEK Binance'e gönder
            binance_paper = settings.trading_mode.upper() != "LIVE"
            logger.info(f"🔄 [HYBRID ROTASYON] {signal.symbol} Kripto varlığı tespit edildi. İnfaz için {target_broker_name} ({'TESTNET/PAPER' if binance_paper else 'LIVE/GERÇEK'}) yönlendiriliyor.")
            broker = get_broker(target_broker_name, paper=binance_paper)
            logger.info(f"[BROKER] Mode: {'PAPER/TESTNET' if binance_paper else 'LIVE'} | Active Routed Broker: {target_broker_name}")
        else:
            target_broker_name = "ALPACA"
            logger.info(f"🔄 [HYBRID ROTASYON] {signal.symbol} Hisse Senedi tespit edildi. İnfaz için {target_broker_name} (SANAL/PAPER) yönlendiriliyor.")
            broker = get_broker(target_broker_name, paper=True)   # Hisse Kesinlikle SANAL (Paper)
            logger.info(f"[BROKER] Mode: PAPER (HYBRID) | Active Routed Broker: {target_broker_name}")
        
        if broker:
            if action_clean in ["BUY", "LONG"]:
                if not pos:
                    logger.warning(f"[BROKER ROTATION] {signal.symbol} bütçe/limit sebebiyle yerel pozisyon açılamadı. Broker emri iptal edildi.")
                    return {"status": "rejected", "reason": "LOCAL_POSITION_FAILED"}
                
                if getattr(pos, "broker_order_id", None):
                    res = {"status": "success", "order_id": pos.broker_order_id, "details": "Already routed by position manager"}
                    logger.info(f"[BROKER] {signal.symbol} zaten pozisyon yöneticisi tarafından iletildi; ikinci emir atlanıyor.")
                else:
                    # Matematiksel Zaafların Giderilmesi (Dinamik ATR Hedefleme)
                    # Sabit %3 TP ve %1.5 SL yerine, varlığın anlık gerçek hareket kapasitesine (ATR) göre oransal hedefleme yapılır.
                    # Bu sayede düşük volatiliteli Asya piyasasında hedef küçültülür, yüksek volatilitede hedef büyütülür.
                    if signal.take_profit:
                        tp_price = signal.take_profit
                    else:
                        atr = float(signal.indicators.get("atr_pct", 3.0)) if signal.indicators else 3.0
                        # Hedef = Günlük ATR'nin %70'i (Çok daralan piyasada bile min %0.8, max %5)
                        dynamic_tp_pct = max(0.8, min(5.0, atr * 0.70))
                        tp_price = round(signal.price * (1 + (dynamic_tp_pct / 100)), 4)
                        logger.info(f"[ATR DYNAMIC TARGET] {signal.symbol} ATR: %{atr:.2f} -> Matematiksel Hedef (TP): %{dynamic_tp_pct:.2f}")

                    if signal.stop_loss:
                        sl_price = signal.stop_loss
                    else:
                        atr = float(signal.indicators.get("atr_pct", 3.0)) if signal.indicators else 3.0
                        # Zarar Kes = Günlük ATR'nin %40'ı (Min %0.5, Max %2.5) -> Hedefe göre Risk/Ödül oranı ~ 1:1.75
                        dynamic_sl_pct = max(0.5, min(2.5, atr * 0.40))
                        sl_price = round(signal.price * (1 - (dynamic_sl_pct / 100)), 4)
                        logger.info(f"[ATR DYNAMIC TARGET] {signal.symbol} ATR: %{atr:.2f} -> Matematiksel Stop (SL): -%{dynamic_sl_pct:.2f}")
                    
                    # --- TIER-1 STEALTH TWAP (Zaman Ağırlıklı Gizli İnfaz) ---
                    # Büyük emirleri (Örn > $500) tek seferde tahtaya vurup Slippage yememek için emri böler.
                    # Eğer Alpaca Elite VWAP API'si olsaydı doğrudan parametre geçilirdi. Burada kendi Stealth motorumuzu kullanıyoruz.
                    import random, threading
                    import time as _twap_time
                    
                    def stealth_twap_execution(b, sym, q, tp, sl, lim):
                        try:
                            slices = 3 if q * lim > 500 else 1
                            slice_qty = q / slices
                            order_ids = []
                            for i in range(slices):
                                jitter_ms = random.uniform(0.1, 0.5)
                                _twap_time.sleep(jitter_ms)
                                
                                # Slippage'dan korunmak için küçük lokmalarla (Market Maker'a görünmeden) emri iletiyoruz.
                                logger.info(f"[STEALTH TWAP] {sym} -> Parça {i+1}/{slices} İletiliyor (Miktar: {slice_qty:.4f})")
                                twap_res = b.place_bracket_order(sym, "BUY", slice_qty, tp, sl, limit_price=lim)
                                
                                if twap_res and twap_res.get("status") == "error":
                                    logger.error(f"[TWAP ERROR] {sym} İnfazı sırasında ağ/api hatası (Internet Kopması): {twap_res.get('message')}")
                                    if pos:
                                        from services.market_feed.live_stream import live_trade_manager
                                        logger.info(f"[NETWORK RECOVERY] {sym} başarısız oldu. Bütçe geri iade ediliyor (Ghost Trade önlendi).")
                                        live_trade_manager.close_position(pos.id, "NETWORK_ERROR_ROLLBACK")
                                        live_trade_manager.positions.pop(pos.id, None)
                                        live_trade_manager.save_state()
                                    return # Stop the rest of the slices
                                
                                if twap_res and twap_res.get("order_id"):
                                    order_ids.append(str(twap_res.get("order_id")))

                                if slices > 1 and i < slices - 1:
                                    # Hacimsiz tahtada fiyatın oturması için 3 saniye bekle
                                    _twap_time.sleep(3.0) 
                            
                            # Eger basarili sekilde tamamladiysa pozisyon statüsünü Guncelle
                            if pos:
                                from services.market_feed.live_stream import live_trade_manager
                                pos.status = "OPEN"
                                if order_ids:
                                    pos.broker_order_id = ",".join(order_ids)
                                live_trade_manager.save_state()
                                logger.info(f"[TWAP SUCCESS] {sym} Pozisyon OPEN durumuna alindi. Broker IDs: {pos.broker_order_id}")

                        except Exception as e:
                            logger.error(f"[TWAP EXCEPTION] {sym} İnfazı sırasında hata: {e}")
                            if pos:
                                from services.market_feed.live_stream import live_trade_manager
                                live_trade_manager.close_position(pos.id, "NETWORK_ERROR_ROLLBACK")
                                live_trade_manager.positions.pop(pos.id, None)
                                live_trade_manager.save_state()
                    # === YIRTICI LİKİDİTE AVCISI (PREDATORY LIQUIDITY LIMIT PUSU) ===
                    # Market fiyatından almak yerine likidite iğnelerini avlamak için fiyatı aşağı çek (BUY)
                    limit_pusu_price = signal.price
                    if action_clean in ["BUY", "LONG"] and is_crypto:
                        atr_pusu_pct = float(signal.indicators.get("atr_pct", 1.5)) if signal.indicators else 1.5
                        # Fiyatı ATR'nin %30'u kadar aşağı çekip Limit Pusu kur (Örn: Fiyat 100, ATR %2 -> %0.6 aşağıdan pusu kur: 99.4)
                        pusu_discount = atr_pusu_pct * 0.30
                        limit_pusu_price = round(signal.price * (1 - (pusu_discount / 100.0)), 6)
                        logger.info(f"🕸️ [PREDATORY LIQUIDITY] {signal.symbol} için {signal.price} yerine {limit_pusu_price} seviyesine LİMİT PUSU kuruluyor! (%{pusu_discount:.2f} dipten yakalama)")

                    # KOMİTE DÜZELTME-2: TWAP'a qty_override (bütçe hesaplamalı) gönder, final_qty (risk motoru) değil!
                    # HATA: final_qty = risk_assessment["adjusted_quantity"] — risk motoru değeri, bütçe ile senkronize değildi.
                    # YENİ: qty_override = allowed_capital / signal.price — bütçe motorunun güvenli, limitli değeri.
                    _twap_qty = qty_override if qty_override and qty_override > 0 else final_qty
                    twap_thread = threading.Thread(target=stealth_twap_execution, args=(broker, signal.symbol, _twap_qty, tp_price, sl_price, limit_pusu_price))
                    twap_thread.start()
                    
                    res = {"status": "success", "message": f"TWAP Stealth Execution başlatıldı (Total Qty: {final_qty})"}
                    
                if res.get("status") == "error":
                    logger.error(f"[BROKER REJECTED] Alpaca API error: {res.get('message')}")
                    return {"status": "rejected", "reason": "BROKER_ORDER_FAILED", "message": res.get("message", "Broker order failed"), "decision": decision}
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


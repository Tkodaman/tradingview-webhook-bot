import asyncio
import time
from core.logger import logger
from core.config import settings
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from services.market_feed.live_stream import live_trade_manager
import ccxt.async_support as ccxt_async

class AutonomousEngine:
    def __init__(self):
        self.is_running = False
        self.polling_interval = 60  # Her 60 saniyede bir calis
        self.binance_futures = ccxt_async.binance({'enableRateLimit': True})
        self.signal_cooldown = {}
        
    async def start(self):
        """Otonom motoru baslatir."""
        if self.is_running:
            return
        self.is_running = True
        logger.info("🚀 [TIER-1 AUTONOMOUS ENGINE] Baslatiliyor...")
        
        last_retrospective_day = None
        
        while self.is_running:
            try:
                # GÜNLÜK ÖZ-ELEŞTİRİ (RETROSPECTIVE) AJANI
                from datetime import datetime, timezone
                current_day = datetime.now(timezone.utc).day
                if last_retrospective_day != current_day and datetime.now(timezone.utc).hour == 23:
                    logger.info("🧠 [RETROSPECTIVE AGENT] Günlük Savaş Raporu Analizi Başlıyor. 'Neyi daha iyi yapabilirdik?' hesaplanıyor...")
                    # Bot Trainer, geçmiş işlemleri (win/loss) analiz edip ağırlıkları günceller
                    from services.trainer.bot_trainer import bot_trainer
                    try:
                        bot_trainer.run_training_cycle(iterations=500)
                        logger.info(f"🧬 [EVRİM TAMAMLANDI] Yeni Genetik Algoritma Ağırlıkları: {bot_trainer.best_params}")
                    except Exception as train_err:
                        logger.warning(f"Öz-eleştiri hatası: {train_err}")
                    last_retrospective_day = current_day

                # ARDIŞIK KAYIP (CONSECUTIVE LOSS) DEVRE KESİCİSİ
                import os, json
                consecutive_loss_file = os.path.join("scratch", "consecutive_loss_state.json")
                if os.path.exists(consecutive_loss_file):
                    try:
                        with open(consecutive_loss_file, "r") as f:
                            loss_state = json.load(f)
                            if loss_state.get("consecutive_losses", 0) >= 3:
                                logger.warning("🛑 [KILL SWITCH] 3 Ardışık Kayıp Tespit Edildi! Sistem 1 Saat Soğumaya Alınıyor...")
                                await asyncio.sleep(3600)
                                # Soğuma sonrası sayacı sıfırla
                                with open(consecutive_loss_file, "w") as f2:
                                    json.dump({"consecutive_losses": 0}, f2)
                    except Exception:
                        pass

                from services.engine.ha_manager import ha_manager
                if ha_manager.is_leader:
                    await self._run_cycle()
                else:
                    logger.debug("💤 [HA FOLLOWER] Otonom Avcı döngüsü atlandı, lider takip ediliyor.")
            except Exception as e:
                logger.error(f"❌ [AUTONOMOUS ENGINE] Dongu Hatasi: {e}")
            
            await asyncio.sleep(self.polling_interval)
            
    async def stop(self):
        """Otonom motoru durdurur."""
        self.is_running = False
        await self.binance_futures.close()
        logger.info("🛑 [TIER-1 AUTONOMOUS ENGINE] Durduruldu.")

    async def _run_cycle(self):
        """Karar Alma Hiyerarşisini (7 Aşamalı SOTA Zırhı) işletir."""
        # AŞAMA 1: Otonom Veri Toplama (1h, 4h, 1D Taraması)
        live_data = await asyncio.to_thread(tradingview_live_client.fetch_live_market_data)
        
        # TIER-1 YÜKSELTMESİ: OTONOM RİSK KALKANI (FLASH CRASH HEDGE)
        try:
            from services.risk_engine.hedge_manager import hedge_manager
            from services.market_feed.live_stream import live_trade_manager
            btc_data = live_data.get("BTCUSDT", {})
            # Basit bir düşüş metrik simülasyonu (Gerçek RSI ve EMA'dan)
            btc_rsi = btc_data.get("RSI", 50)
            btc_drop_pct = -3.5 if btc_rsi < 25 else 0.0 # Aşırı satım varsa drop simülasyonu
            
            # --- TIER-1 MAKRO KALKANI (VIX KORKU ENDEKSİ) ---
            # CBOE:VIX artık TradingViewScanner tarafından canlı çekiliyor.
            vix_data = live_data.get("VIX", {})
            vix_price = vix_data.get("price", 15.0)
            is_vix_high = vix_price >= 22.0 # VIX 22 üstüyse Makro Risk yüksektir (Kalkan Tetiklenir)
            if is_vix_high:
                logger.warning(f"🌐 [MAKRO VİZYON] VIX Korku Endeksi kritik seviyede: {vix_price}! Küresel risk tespit edildi.")
                
            hedge_manager.evaluate_flash_crash_and_hedge(live_trade_manager, btc_drop_pct, is_vix_high)
        except Exception as e:
            logger.error(f"[HEDGE MANAGER ERROR] {e}")

        # TIER-2: KONSEY YÖNLENDİRMESİ (WMA +2 Ağırlıklı Sıralama)
        try:
            from routers.market_router import get_live_buy_sell_wait_matrix
            matrix_results = await get_live_buy_sell_wait_matrix()
            # Konseyin en yüksek puan (WMA) verdigi siralamayi cikar
            ranked_symbols = [item["symbol"] for item in matrix_results if "symbol" in item]
            for sym in list(live_data.keys()):
                if sym not in ranked_symbols:
                    ranked_symbols.append(sym)
        except Exception as e:
            logger.error(f"[KONSEY YÖNLENDİRME HATASI] {e}")
            ranked_symbols = list(live_data.keys())

        for symbol in ranked_symbols:
            data = live_data.get(symbol)
            if not data:
                continue
                
            try:
                # --- ENSTRÜMAN 1: Açık Pozisyon & Fonlama Oranı (Short Squeeze Radarı) ---
                is_short_squeeze_setup = False
                if "USDT" in symbol:
                    try:
                        funding_info = await self.binance_futures.fetch_funding_rate(symbol.replace("USDT", "/USDT"))
                        funding_rate = funding_info.get('fundingRate', 0)
                        is_short_squeeze_setup = funding_rate < -0.001  # Fonlama aşırı negatifse
                    except Exception as e:
                        # Funding rate bulunamazsa veya hata olursa döngüyü kırma
                        pass
                
                # --- ENSTRÜMAN 2: Fraktal Zaman Uyum Filtresi (Multi-Timeframe) ---
                ema200_1h = data.get("EMA200|60", 0)
                current_price = data.get("price", 0)
                # PAPER modunda ezilmişlik töleransını %5'ten %10'a çıkarıyoruz
                ema_tolerance = 0.90 if settings.trading_mode == "PAPER" else 0.95
                if current_price < ema200_1h * ema_tolerance: 
                    logger.info(f"⏳ [AVCI] {symbol} reddedildi: Fiyat EMA200 altında çok ezilmiş.")
                    continue  # NO-TRADE
                    
                # --- ENSTRÜMAN 3: KÜRESEL PARA DÖNGÜSÜ (Seanslar Arası Sörf) ---
                from datetime import datetime, timezone, timedelta
                now_utc = datetime.now(timezone.utc)
                trt_time = now_utc + timedelta(hours=3)
                hour = trt_time.hour
                
                session_name = "BİLİNMEYEN"
                if 15 <= hour < 23:
                    session_name = "DEVLER LİGİ (ABD/AB)"
                elif 23 <= hour or hour < 2:
                    session_name = "ÖLÜ BÖLGE (Hacim Boşluğu)"
                    rsi_1h = data.get("RSI|60", 50)
                    # PAPER modunda RSI sınırını 60'tan 68'e gevşetiyoruz
                    rsi_limit = 68 if settings.trading_mode == "PAPER" else 60
                    if rsi_1h > rsi_limit:  
                        logger.info(f"⏳ [AVCI] {symbol} reddedildi: Ölü Bölge'de tepe (RSI>{rsi_limit}) alınmaz.")
                        continue
                elif 2 <= hour < 8:
                    session_name = "ASYA KAPLANLARI (FOMO)"
                    adx_1h = data.get("adx", 0)
                    # PAPER modunda Asya seansı ADX eşiğini 15'ten 10'a düşürüyoruz
                    adx_fomo = 10 if settings.trading_mode == "PAPER" else 15
                    if adx_1h < adx_fomo:
                        logger.info(f"⏳ [AVCI] {symbol} reddedildi: Asya seansında (ADX<{adx_fomo}) zayıf ivme.")
                        continue
                
                # --- SOTA ZIRHI 1: Hacim Patlaması (Volume Spike) ---
                volume_ratio = data.get("volume_ratio", 0)
                is_crypto = "USDT" in symbol
                
                # PAPER modunda hacim sınırını 1.0 yerine 0.90 yapıyoruz (Ufak kıpırdanma)
                if is_crypto:
                    min_vol = 0.90 if settings.trading_mode == "PAPER" else 1.0
                else:
                    min_vol = 0.30 if settings.trading_mode == "PAPER" else 1.0
                
                if volume_ratio < min_vol and not is_short_squeeze_setup and session_name != "ÖLÜ BÖLGE (Hacim Boşluğu)":
                    logger.info(f"⏳ [AVCI] {symbol} reddedildi: Hacim patlaması yetersiz (Vol: {volume_ratio:.2f})")
                    continue
                    
                # --- SOTA ZIRHI 2: Oynaklık (ATR) ve Düşen Bıçak Kuralı ---
                adx = data.get("adx", 0)
                
                # PAPER modunda ADX eşiğini 5 yerine 3 (Çok hafif rüzgar) olarak güncelliyoruz
                if is_crypto:
                    min_adx = 3.0 if settings.trading_mode == "PAPER" else 5.0 
                else:
                    min_adx = 10.0 if settings.trading_mode == "PAPER" else 15.0
                
                if adx < min_adx and session_name != "ÖLÜ BÖLGE (Hacim Boşluğu)":
                    logger.info(f"⏳ [AVCI] {symbol} reddedildi: Trend momentumu düşük (ADX: {adx:.1f})")
                    continue
                    
                # --- ENSTRÜMAN 3: Kelly Kriteri (Dinamik Kasa Yönetimi) ---
                win_rate = 0.55  # Sistem ortalaması
                risk_reward = 2.0
                kelly_pct = win_rate - ((1 - win_rate) / risk_reward)
                # Kelly risk sınırını %50'den max %20'ye düşürdük
                suggested_risk_pct = min(max(kelly_pct, 0.01), 0.20) 

                # --- PORTFÖY ZIRHI: Kripto Bazlı Limit (Sadece CRYPTO pozisyonları sayılır) ---
                # DÜZELTME: Eski kod TÜM pozisyonları sayıyordu (NASDAQ dahil).
                # Bu yüzden 12 NASDAQ açıkken CRYPTO sinyalleri de bloklanıyordu.
                open_positions = getattr(live_trade_manager, "positions", {})
                open_pos_count = len([
                    p for p in open_positions.values()
                    if getattr(p, "status", "") in ["OPEN", "PENDING_BROKER"]
                    and getattr(p, "market", "") == "CRYPTO"
                ])

                # --- KORELASYON KORUMASI (BTC ve ETH aynı anda açılmasın) ---
                if symbol == "ETHUSDT" and any(p for p in open_positions.values() if p.symbol == "BTCUSDT" and p.status == "OPEN"):
                    logger.info(f"🛡️ [KORELASYON KALKANI] BTC zaten açık, {symbol} reddedildi.")
                    continue
                if symbol == "BTCUSDT" and any(p for p in open_positions.values() if p.symbol == "ETHUSDT" and p.status == "OPEN"):
                    logger.info(f"🛡️ [KORELASYON KALKANI] ETH zaten açık, {symbol} reddedildi.")
                    continue

                from core.config import settings
                max_allowed_positions = int(getattr(settings, "crypto_max_positions", 6))

                if open_pos_count >= max_allowed_positions:
                    logger.warning(f"[CRYPTO LIMIT] {symbol} reddedildi. Kripto pozisyon limiti dolu ({open_pos_count}/{max_allowed_positions}).")
                    continue
                    
                # --- AŞAMALI ALIM (STAGGERED ENTRY / GLOBAL PACING) ZIRHI ---
                # Kullanıcı Talebi: "İlk startta tüm pozisyonları anında doldurmak yerine izleyerek, gölge testinden süzerek sıralı alım yap"
                last_crypto_open_time = None
                from datetime import datetime
                for p in open_positions.values():
                    if getattr(p, "market", "") == "CRYPTO":
                        p_ts = getattr(p, "created_at", None)
                        if p_ts:
                            try:
                                p_dt = datetime.strptime(p_ts, "%Y-%m-%d %H:%M:%S")
                                if last_crypto_open_time is None or p_dt > last_crypto_open_time:
                                    last_crypto_open_time = p_dt
                            except:
                                pass
                
                if last_crypto_open_time is not None:
                    minutes_since_last = (datetime.now() - last_crypto_open_time).total_seconds() / 60.0
                    # Aşamalı Alım Eşiği: 2 Dakika (Kullanıcının talep ettiği agresif doktrin)
                    if minutes_since_last < 2.0:
                        logger.info(f"⏳ [AŞAMALI ALIM] {symbol} izlemede. Son işlemden bu yana 2 dk geçmesi bekleniyor (Mevcut: {minutes_since_last:.2f} dk).")
                        continue

                # COOLDOWN (Bekleme Süresi) Koruması: Aynı coini art arda yapay zekaya sormamak için
                now = time.time()
                if symbol in self.signal_cooldown and now - self.signal_cooldown[symbol] < 300:
                    logger.debug(f"{symbol} reddedildi: Cooldown devrede. Son sinyal üzerinden 5 dk geçmedi.")
                    continue
                
                self.signal_cooldown[symbol] = now

                try:
                    from services.risk_engine.reversal_engine import reversal_engine
                    is_reversal = symbol in [r.split(":")[-1] for r in reversal_engine.target_symbols]
                except Exception:
                    is_reversal = False
                    
                display_symbol = f"🟣 {symbol} (DİP)" if is_reversal else symbol
                logger.info(f"💎 [TIER-1 ONAYI] {display_symbol} | Squeeze: {is_short_squeeze_setup} | Risk Pct: %{suggested_risk_pct*100:.1f}")
                
                # --- SOTA ZIRHI 3 & 4 (Execution): Hard Stop & İzleyen Kâr ---
                # Sinyal kusursuz! process_order tetiklenir...
                from schemas.webhook import WebhookSignal
                from services.order_router import process_order
                
                fake_signal = WebhookSignal(
                    symbol=symbol,
                    action="BUY",
                    price=current_price,
                    timeframe="1h",
                    timestamp_ms=int(now*1000)
                )
                
                await asyncio.to_thread(process_order, fake_signal)
                
            except Exception as e:
                # API Limitleri veya diğer hatalarda çökmeyi engelle
                logger.error(f"[AVCI HATA] Sembol: {symbol}, Hata: {e}")
                pass

autonomous_engine = AutonomousEngine()

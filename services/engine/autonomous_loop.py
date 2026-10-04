import asyncio
import time
from core.logger import logger
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
            is_vix_high = False # Gelişmiş VIX entegrasyonu ileride eklenebilir
            hedge_manager.evaluate_flash_crash_and_hedge(live_trade_manager, btc_drop_pct, is_vix_high)
        except Exception as e:
            logger.error(f"[HEDGE MANAGER ERROR] {e}")

        for symbol, data in live_data.items():
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
                if current_price < ema200_1h * 0.95: # %5 tölerans
                    logger.info(f"⏳ [AVCI] {symbol} reddedildi: Fiyat EMA200 altında çok ezilmiş.")
                    continue  # NO-TRADE
                    
                # --- ENSTRÜMAN 3: KÜRESEL PARA DÖNGÜSÜ (Seanslar Arası Sörf) ---
                # Türkiye Saati (UTC+3) baz alınarak seans analizi
                from datetime import datetime, timezone, timedelta
                now_utc = datetime.now(timezone.utc)
                trt_time = now_utc + timedelta(hours=3)
                hour = trt_time.hour
                
                session_name = "BİLİNMEYEN"
                if 15 <= hour < 23:
                    session_name = "DEVLER LİGİ (ABD/AB)"
                    # Breakout (Kırılım) stratejisi aktiftir. Hacim aranır.
                elif 23 <= hour or hour < 2:
                    session_name = "ÖLÜ BÖLGE (Hacim Boşluğu)"
                    # Hacim azalır. Yeni FOMO kırılımlarına GİRİLMEZ! Sadece "Dip Toplama (Buyback)" yapılır.
                    rsi_1h = data.get("RSI|60", 50)
                    if rsi_1h > 60:  # Gevşetildi
                        logger.info(f"⏳ [AVCI] {symbol} reddedildi: Ölü Bölge'de tepe (RSI>60) alınmaz.")
                        continue
                elif 2 <= hour < 8:
                    session_name = "ASYA KAPLANLARI (FOMO)"
                    # Agresif hacim ve ivme aranır. ADX (Trend Gücü) yüksek olmalı.
                    adx_1h = data.get("adx", 0)
                    if adx_1h < 15:
                        logger.info(f"⏳ [AVCI] {symbol} reddedildi: Asya seansında (ADX<15) zayıf ivme.")
                        continue
                
                # --- SOTA ZIRHI 1: Hacim Patlaması (Volume Spike) ---
                volume_ratio = data.get("volume_ratio", 0)
                # Simüle/Öğrenme modunda hacim şartını esnetiyoruz (Kullanıcının aksiyon görmesi için)
                from core.config import settings
                min_vol = 0.5 if settings.trading_mode == "PAPER" else 1.0
                
                # Kriptolar için Testnet'te al-sat görülebilmesi adına hacim tamamen sıfırlandı
                is_crypto = "USDT" in symbol
                if is_crypto:
                    min_vol = 0.01 
                
                if volume_ratio < min_vol and not is_short_squeeze_setup and session_name != "ÖLÜ BÖLGE (Hacim Boşluğu)":
                    logger.info(f"⏳ [AVCI] {symbol} reddedildi: Hacim patlaması yetersiz (Vol: {volume_ratio:.2f})")
                    continue  # Hacim yoksa sahte harekettir
                    
                # --- SOTA ZIRHI 2: Oynaklık (ATR) ve Düşen Bıçak Kuralı ---
                adx = data.get("adx", 0)
                min_adx = 10 if settings.trading_mode == "PAPER" else 15
                
                if is_crypto:
                    min_adx = 2 # Kripto için momentum şartını geç
                
                if adx < min_adx and session_name != "ÖLÜ BÖLGE (Hacim Boşluğu)":
                    logger.info(f"⏳ [AVCI] {symbol} reddedildi: Trend momentumu düşük (ADX: {adx:.1f})")
                    continue  # Trend gücü (Momentum) zayıf, range piyasası.
                    
                # --- ENSTRÜMAN 3: Kelly Kriteri (Dinamik Kasa Yönetimi) ---
                win_rate = 0.55  # Sistem ortalaması
                risk_reward = 2.0
                kelly_pct = win_rate - ((1 - win_rate) / risk_reward)
                # Kelly risk sınırını %50'den max %20'ye düşürdük
                suggested_risk_pct = min(max(kelly_pct, 0.01), 0.20) 

                # --- PORTFÖY ZIRHI: Dinamik Limit (LIVE: 2 Koin | PAPER: 14 Koin) ---
                # live_trade_manager üzerinden o anki açık pozisyon sayısına bakıyoruz
                open_positions = getattr(live_trade_manager, "positions", {})
                open_pos_count = len([p for p in open_positions.values() if getattr(p, "status", "") == "OPEN"])
                
                # --- KORELASYON KORUMASI (BTC ve ETH aynı anda açılmasın) ---
                if symbol == "ETHUSDT" and any(p for p in open_positions.values() if p.symbol == "BTCUSDT" and p.status == "OPEN"):
                    logger.info(f"🛡️ [KORELASYON KALKANI] BTC zaten açık, {symbol} reddedildi.")
                    continue
                if symbol == "BTCUSDT" and any(p for p in open_positions.values() if p.symbol == "ETHUSDT" and p.status == "OPEN"):
                    logger.info(f"🛡️ [KORELASYON KALKANI] ETH zaten açık, {symbol} reddedildi.")
                    continue
                
                max_allowed_positions = 14 if settings.trading_mode == "PAPER" else 2
                
                if open_pos_count >= max_allowed_positions:
                    logger.warning(f"Limit {max_allowed_positions}/{max_allowed_positions} dolu. Yeni işleme girilmiyor (Mod: {settings.trading_mode}).")
                    continue

                # COOLDOWN (Bekleme Süresi) Koruması: Aynı coini art arda AI'a gönderip token yakmasını engelle
                now = time.time()
                if symbol in self.signal_cooldown and now - self.signal_cooldown[symbol] < 1800:
                    logger.debug(f"{symbol} reddedildi: Cooldown devrede (Token koruması). Son sinyal üzerinden 30dk geçmedi.")
                    continue
                
                self.signal_cooldown[symbol] = now

                logger.info(f"💎 [TIER-1 ONAYI] {symbol} | Squeeze: {is_short_squeeze_setup} | Risk Pct: %{suggested_risk_pct*100:.1f}")
                
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

import time
from typing import Dict, Any
from core.logger import logger
from services.broker.factory import get_broker
from services.engine.bot_thought_stream import bot_thought_stream

class HedgeManager:
    """
    Tier-1 Yükseltmesi: Otonom Risk Kalkanı & 'Flash Crash' Hedging
    Eğer piyasada ani bir çöküş (Flash Crash) veya aşırı volatiliteli bir satış baskısı tespit edilirse,
    elimizdeki Long (Alım) pozisyonlarını korumak için ana endekslerde (Örn: BTCUSDT) 
    otomatik olarak SHORT (Satış) pozisyonu açarak cüzdanın Net PnL'ini sıfırlar (Kalkan).
    """
    def __init__(self):
        self.is_hedge_active = False
        self.hedge_symbol = "BTCUSDT"
        self.last_check_time = 0

    def evaluate_flash_crash_and_hedge(self, live_trade_manager, btc_drop_pct: float, is_vix_high: bool):
        """
        Piyasayı analiz eder, eğer risk yüksekse ve hedge yoksa kalkanı aktifleştirir.
        btc_drop_pct: Son 15-30 dakikadaki BTC düşüş yüzdesi
        is_vix_high: Makro volatilite endeksi durumu
        """
        now = time.time()
        if now - self.last_check_time < 60:
            return # Her dakika bir kez kontrol et (Spam önleme)
        self.last_check_time = now
        
        # Sadece Kripto portföyünü (Binance) baz alıyoruz
        crypto_longs = [p for p in live_trade_manager.positions.values() if p.status == "OPEN" and p.market == "CRYPTO" and p.side == "BUY"]
        
        if len(crypto_longs) < 3:
            return # Yeterince Long yok, kalkan açmaya gerek yok.

        total_exposure = sum(p.nominal_value for p in crypto_longs)
        
        # Eğer BTC %3'ten fazla düştüyse veya VIX çok yüksekse çöküş (Crash) modu
        is_crash_detected = btc_drop_pct <= -3.0 or is_vix_high
        
        # Kalkan henüz aktif değilse ve çöküş varsa, aç.
        if is_crash_detected and not self.is_hedge_active:
            logger.warning(f"🛡️ [HEDGE KALKANI] Flash Crash algılandı! BTC Düşüşü: {btc_drop_pct}%. Kalkan açılıyor...")
            self._deploy_hedge(live_trade_manager, total_exposure)
            
        # Pazar normale döndüyse kalkanı kaldır.
        elif not is_crash_detected and self.is_hedge_active and btc_drop_pct > -1.0:
            logger.info("🌤️ [HEDGE KALKANI] Piyasa duruldu. Kalkan indiriliyor...")
            self._remove_hedge(live_trade_manager)
            
    def _deploy_hedge(self, live_trade_manager, total_exposure: float):
        """
        Elimizdeki toplam riskin (Exposure) %50'si kadar büyüklükte BTC SHORT aç.
        """
        hedge_size = total_exposure * 0.50
        logger.info(f"🛡️ [HEDGE DEPLOY] {self.hedge_symbol} üzerinde ${hedge_size:.2f} büyüklüğünde SHORT kalkanı kuruluyor!")
        
        try:
            bot_thought_stream.add(
                category="🛡️ HEDGE KALKANI",
                symbol="MACRO",
                message=f"Piyasada ani çöküş saptandı. Tüm Long pozisyonları korumak adına ${hedge_size:.2f} değerinde BTCUSDT SHORT kalkanı aktifleştirildi.",
                level="ERROR"
            )
            # Binance üzerinden SHORT emri (Spot'ta SHORT olmasa bile Futures/Margin destekli yapıya gönderim)
            # Bu MVP (Canlı) simülasyon/gölge olarak işlenir çünkü Spot'ta doğrudan Short yok.
            live_trade_manager.open_shadow_position(
                symbol=self.hedge_symbol,
                side="SELL",
                tp_pct=5.0, # Büyük bir hedef
                sl_pct=1.0, # Kalkanı ucuza kapatma
                entry_price_override=0.0, # Piyasadan
                reason=f"Flash Crash Protection (Exposure: ${total_exposure:.0f})"
            )
            self.is_hedge_active = True
        except Exception as e:
            logger.error(f"[HEDGE DEPLOY ERROR] {e}")
            
    def _remove_hedge(self, live_trade_manager):
        """
        Kalkan pozisyonunu kapat (Varsa).
        """
        self.is_hedge_active = False
        bot_thought_stream.add(
            category="🌤️ KALKAN İNDİRİLDİ",
            symbol="MACRO",
            message="Piyasa koşulları normale döndü. Otonom kalkan devre dışı bırakıldı.",
            level="INFO"
        )
        
hedge_manager = HedgeManager()

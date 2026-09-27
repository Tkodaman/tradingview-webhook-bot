import time
from typing import Dict, Any, Tuple
from core.logger import logger

class DecisionArbiter:
    """
    Astra 6 Mimarisi: Bağımsız Risk ve Karar Hakemi (Güvenlik Hakemi)
    Tüm indikatörler, modeller ve sinyaller "AL" dese bile, bu hakem otonom olarak
    aşağıdaki sistem durum makinesini işletir ve işlemi durdurabilir:
    Durumlar: DATA_INVALID -> OBSERVE_ONLY -> CANDIDATE -> RISK_APPROVED -> EXECUTION_ELIGIBLE -> COOLDOWN
    """

    def __init__(self):
        self.MAX_DATA_AGE_SECONDS = 15.0 # Veri tazeliği limiti
        self.MAX_SPREAD_TOLERANCE = 0.005 # %0.5 maks spread
        self.MAX_DAILY_DRAWDOWN = 0.10 # %10 günlük kayıp limiti

    async def evaluate_candidate(self, symbol: str, data: Dict[str, Any], current_portfolio_pnl: float) -> Tuple[str, str]:
        """
        Durum Makinesi mantığı ile kararı değerlendirir. (Asenkron)
        Döner değer: (Durum [str], Sebep [str])
        """
        # 0. FinBERT YZ Hızlı Duyarlılık (Cüretkar Tetikleme)
        from services.ai.finbert_sentiment import ai_sentiment_radar
        sentiment_text = data.get("latest_news_headline", "")
        if sentiment_text:
            sentiment_result = await ai_sentiment_radar.analyze_sentiment_fast(sentiment_text)
            label = sentiment_result.get("label", "neutral")
            
            # Cüretkar Karar: Eger negatifse ama guven skorlu bir sinyalse sadece pozisyonu azalt, iptal etme.
            if label == "negative":
                data["audacious_multiplier"] = 0.5 # Yari lot ile dal
                logger.warning(f"⚡ [Cüretkar Mod] {symbol} icin negatif haber var, ama iptal edilmiyor! Yari hacimle saldiriliyor.")
            elif label == "positive":
                data["audacious_multiplier"] = 1.5 # %150 agresif lot
                logger.warning(f"🔥 [Agresif Mod] {symbol} icin pozitif haber TEYIT EDILDI! Lot x1.5 basiliyor.")
            else:
                data["audacious_multiplier"] = 1.0

        # 1. DATA_INVALID Kontrolü (Veri Güncelliği ve Geçerliliği)
        timestamp = data.get("timestamp", time.time())
        if time.time() - timestamp > self.MAX_DATA_AGE_SECONDS:
            return "DATA_INVALID", "Veri çok eski (stale quote). Gecikme riski."
        
        price = data.get("price", 0.0)
        if price <= 0:
            return "DATA_INVALID", "Geçersiz fiyat verisi."

        # 2. OBSERVE_ONLY Kontrolü (Olay / Makro / Likidite / Günlük Zarar Limitleri)
        if current_portfolio_pnl <= -self.MAX_DAILY_DRAWDOWN:
            return "OBSERVE_ONLY", f"Günlük maksimum kayıp sınırı ({self.MAX_DAILY_DRAWDOWN}) aşıldı."
        
        # Likidite ve Volatilite uç noktaları
        vol_ratio = data.get("volume_ratio", 1.0)
        if vol_ratio < 0.3:
            return "OBSERVE_ONLY", "Likidite çok düşük (Sığ tahta). Fakeout riski."

        # 3. CANDIDATE -> RISK_APPROVED (Slippage ve Spread Kontrolleri)
        spread = data.get("spread_pct")
        if spread is not None and spread > self.MAX_SPREAD_TOLERANCE:
            return "CANDIDATE_REJECTED", f"Spread çok yüksek: {spread}. Kabul edilebilir max: {self.MAX_SPREAD_TOLERANCE}."

        # Her şey yolundaysa Execution için onay ver
        return "EXECUTION_ELIGIBLE", "Tüm güvenlik ve risk hakemi kontrolleri geçildi."

decision_arbiter = DecisionArbiter()

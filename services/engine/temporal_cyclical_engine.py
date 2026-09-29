from datetime import datetime
import pytz

class TemporalCyclicalEngine:
    def __init__(self):
        self.tz = pytz.timezone("Europe/Istanbul") # TSİ (Türkiye Saati)

    def get_temporal_modifiers(self, symbol, market_type="CRYPTO", current_time=None):
        """
        Anlık zamanı ve günü analiz ederek, botun skorlamasına ve stop-loss 
        seviyelerine etki edecek zamansal (temporal) ve döngüsel (cyclical) çarpanları döner.
        """
        if current_time is None:
            current_time = datetime.now(self.tz)
            
        day_of_week = current_time.weekday() # 0: Pazartesi, 6: Pazar
        hour = current_time.hour
        
        modifiers = {
            "score_bonus": 0,
            "sl_tighten_pct": 1.0,  # 1.0 = Normal SL, 0.5 = Yarı yarıya daralt (Daha sıkı stop)
            "lot_multiplier": 1.0,
            "temporal_reason": ""
        }

        # 1. HAFTA SONU DİNAMİKLERİ (Cuma Kapanış ve Pazar Açılış)
        if day_of_week == 4 and hour >= 22:
            # Cuma TSİ 22:00 sonrası: Hafta sonu likidite boşluğu başlıyor (Weekend Dump riski)
            modifiers["score_bonus"] -= 3
            modifiers["sl_tighten_pct"] = 0.7  # Stopları daralt
            modifiers["temporal_reason"] = "Cuma Kapanış (Hafta sonu likidite boşluğu riski). Kalkan devrede."
            
        elif day_of_week == 6 and hour >= 23:
            # Pazar TSİ 23:00 sonrası: Asya açılışı ve Gap kapatma rallisi (Volatility)
            modifiers["score_bonus"] += 2
            modifiers["temporal_reason"] = "Pazar Asya Açılışı (Gap Avcılığı). Volatilite yüksek, bonus aktif."

        # 2. HAFTA İÇİ DÖNGÜSEL TEPKİLER (Bloody Monday vs Trend Tuesday)
        if day_of_week == 0 and hour < 16:
            # Pazartesi ABD açılışı (16:30) öncesi "Stop-Hunt" riskleri
            modifiers["score_bonus"] -= 1
            modifiers["lot_multiplier"] = 0.8
            modifiers["temporal_reason"] = "Kanlı Pazartesi (Bloody Monday) Silkeleme riski. Temkinli lot."
            
        elif day_of_week in [1, 2]: # Salı ve Çarşamba (Trend Günleri)
            modifiers["score_bonus"] += 2
            modifiers["lot_multiplier"] = 1.0
            modifiers["temporal_reason"] = "Haftalık Ana Trend Günü (Salı/Çarş). Cüretkar Mod aktif."
            
        elif day_of_week in [3, 4] and hour < 22: # Perşembe / Cuma kâr alma (Profit Taking)
            # Kâr alma günleri: Sıkı stop
            modifiers["sl_tighten_pct"] = 0.8
            modifiers["temporal_reason"] = "Hafta sonuna yaklaşırken Kâr Alma (Profit Taking) döngüsü. Stop daraltıldı."

        # 3. KORELASYON ZAMANI (Pre-Market)
        if market_type == "CRYPTO" and day_of_week < 5 and (11 <= hour <= 16):
            # TSİ 11:00 - 16:30 arası: Geleneksel Pre-Market (Örn: NASDAQ) ralli yapıyorsa
            # Kripto bunu front-run eder. 
            modifiers["score_bonus"] += 2
            modifiers["temporal_reason"] = "NASDAQ Pre-Market saatleri. Kripto cephesinde Front-Running (önden fiyatlama) desteği."

        return modifiers

temporal_cyclical_engine = TemporalCyclicalEngine()

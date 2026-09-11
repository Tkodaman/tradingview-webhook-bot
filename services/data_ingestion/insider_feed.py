import random
import time
from typing import Dict, Any, List

class CorporateInsiderTracker:
    def __init__(self):
        # Gerçek bir API'ye bağlanana kadar simülasyon modunda çalışır
        self.simulation_mode = True
        
        # Otonom simülasyon için kurgusal insider alımları ve satımları veritabanı
        self._mock_data_pool = {
            "BUY": [
                "CEO {shares} lot hisse alımı bildirdi. (Form 4).",
                "Yönetim Kurulu Üyesi portföyüne net {shares} lot ekledi.",
                "CFO piyasa fiyatından {shares} lot alım yaptı.",
                "Kurucu Ortak {shares} lot stratejik alım gerçekleştirdi."
            ],
            "SELL": [
                "CEO opsiyon kullanımı sonrası {shares} lot hisse sattı (Form 4).",
                "CFO vergi ödemeleri için {shares} lot satış yaptı.",
                "Yönetici otomatik satış (10b5-1) planı kapsamında {shares} lot elden çıkardı."
            ]
        }

    def fetch_insider_transactions(self, symbol: str) -> Dict[str, Any]:
        """
        Belirtilen varlık için son güncel Corporate Insider işlemlerini (Yönetici alım/satımları) döndürür.
        """
        # Eğer gerçek bir API eklenecekse buraya (Örn: Finnhub, SEC EDGAR) request eklenecek.
        if not self.simulation_mode:
            # TODO: Add real API fetching logic here
            pass

        # Simülasyon Senaryosu (Mock Data Generator)
        # Hisselerin bazılarına rastgele "Güçlü Alım" veya "Zayıf Satış" senaryoları atayalım
        return self._generate_simulated_insider_signal(symbol)

    def _generate_simulated_insider_signal(self, symbol: str) -> Dict[str, Any]:
        """Gerçekçi bir Insider sinyali simülatörü."""
        random.seed(int(time.time() * 1000) + hash(symbol)) # Pseudo-random ama sembole özgü kısa süreli tutarlılık
        
        # Kriptolar için Insider olmaz (genelde on-chain balina hareketleri olur), ama şimdilik "Whale/Insider" gibi genelleyebiliriz.
        is_crypto = symbol.endswith("USDT") or symbol in ["BTC", "ETH", "SOL", "BNB"]
        
        # %60 ihtimalle NÖTR (Yeni bir işlem yok)
        action_chance = random.random()
        if action_chance < 0.60:
            return {
                "symbol": symbol,
                "has_insider_activity": False,
                "signal_type": "NEUTRAL",
                "net_volume": 0,
                "confidence_modifier": 0.0,
                "qty_multiplier": 1.0,
                "message": "Son 72 saatte kayda değer bir içeriden öğrenen/yönetici işlemi yok."
            }
            
        # %40 ihtimalle aktivite var
        is_buy = random.random() > 0.4 # %60 alım, %40 satış (Genelde yönetim satışı rutindir, alım pozitiftir)
        
        if is_crypto:
            title_buy = ["Balina Cüzdanı", "Kurumsal Fon", "Vakıf (Foundation)"]
            title_sell = ["Büyük Madenci Cüzdanı", "Balina Cüzdanı", "Vakıf (Foundation)"]
            subject = random.choice(title_buy if is_buy else title_sell)
            shares = random.randint(100, 5000)
            if is_buy:
                msg = f"{subject} on-chain ağında {shares} {symbol} transfer edip kilitledi (Birikim)."
            else:
                msg = f"{subject} borsaya {shares} {symbol} transfer etti (Satış Baskısı)."
        else:
            shares = random.randint(5000, 50000)
            pool = self._mock_data_pool["BUY"] if is_buy else self._mock_data_pool["SELL"]
            msg = random.choice(pool).format(shares=f"{shares:,}")

        if is_buy:
            return {
                "symbol": symbol,
                "has_insider_activity": True,
                "signal_type": "INSIDER_BUY",
                "net_volume": shares,
                "confidence_modifier": +0.30, # Alım pozitif güven verir
                "qty_multiplier": 1.30,       # %30 Lot artır
                "message": f"{symbol}: {msg}"
            }
        else:
            return {
                "symbol": symbol,
                "has_insider_activity": True,
                "signal_type": "INSIDER_SELL",
                "net_volume": -shares,
                "confidence_modifier": -0.20, # Satış negatif güven verir
                "qty_multiplier": 0.80,       # %20 Lot daralt
                "message": f"{symbol}: {msg}"
            }

insider_tracker = CorporateInsiderTracker()

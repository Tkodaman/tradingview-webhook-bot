import logging

logger = logging.getLogger(__name__)

class RedFlagGuardian:
    """
    Kırmızı Bayrak (Red Flag) Haber ve Duyarlılık Kilidi.
    Teknik analiz körlüğünü engellemek için, varlık üzerinde ani gelişen
    felaket haberlerini (Hack, Scam, İflas, SEC Davası vb.) tarar.
    Radardaki puanı %100 bile olsa, kırmızı bayrak varsa sistemi kilitler.
    """
    def __init__(self):
        self.red_flag_keywords = [
            "hack", "scam", "fraud", "delist", "iflas", "sec", "dava", 
            "bankruptcy", "investigation", "exploit", "rug pull", "lawsuit", "hacked"
        ]
        
    def check_red_flags(self, symbol: str, latest_news: str = "") -> dict:
        """
        Sosyal medya veya haber API'sinden gelen son 1 saatlik veriyi tarar.
        (Burada sistem gerçek veri gelene kadar mock veya external source'u simüle eder).
        """
        # Şimdilik "gerçek bir haber entegrasyonu" olmadığı için, parametre üzerinden
        # gelen metni tarıyoruz. Eğer bir haber string'inde tehlikeli kelime geçerse kilitler.
        
        if not latest_news:
            return {"is_safe": True, "reason": "Haber akışı temiz."}
            
        lower_news = latest_news.lower()
        for kw in self.red_flag_keywords:
            if kw in lower_news:
                logger.warning(f"🚨 [RED FLAG KİLİDİ] {symbol} tahtasında '{kw}' kelimesi tespit edildi! Teknik veriler YALANCI (Tuzak) olabilir. İşlem reddedildi.")
                return {
                    "is_safe": False, 
                    "reason": f"KIRMIZI BAYRAK TESPİTİ: Son 1 saatlik haberlerde/sosyal medyada '{kw.upper()}' uyarısı var. Manipülasyon riski!"
                }
                
        return {"is_safe": True, "reason": "Haber taraması temiz, kırmızı bayrak yok."}

red_flag_guardian = RedFlagGuardian()

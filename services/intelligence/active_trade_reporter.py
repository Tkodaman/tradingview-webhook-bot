import asyncio
import time
from typing import List, Dict, Any
from core.logger import logger
import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

async def ask_gemini(prompt: str) -> str:
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini Hata (Active Reporter): {e}")
        return f"Rapor Hazırlanamadı: {e}"
class ActiveTradeReporter:
    def __init__(self, max_history=10):
        self.reports: List[Dict[str, Any]] = []
        self.max_history = max_history

    async def generate_and_store_report(self, symbol: str, price: float, tp1: float, tp2: float, sl: float, action: str = "BUY", status: str = "SUCCESS", error_msg: str = None):
        """
        İşlem açıldığı anda arka planda çalışarak Yüce Divan komite tartışması eşliğinde
        4 adım ötesini düşünen net bir harekat raporu üretir.
        """
        try:
            if status == "SUCCESS":
                prompt = f"""
Komutanın emriyle az önce {symbol} varlığında {price} fiyatından {action} pozisyonu başarıyla açıldı!
Hedefler -> TP1: {tp1:.4f}, TP2: {tp2:.4f}, SL (Zarar Kes): {sl:.4f}.

SENİN GÖREVİN: 3 farklı profesyonel ajan (Makro Stratejist, Kantitatif Algoritma Uzmanı ve Kriz Yöneticisi) olarak kendi içinizde bu işlemi masaya yatırmak ve Komutana tek bir KUSURSUZ "HAREKAT RAPORU" sunmak.

Şartlar ve İçerik:
1. Kesinlik ve Netlik: Yuvarlak kelimeler kullanma. "Çıkabilir" yerine "Hedef vurulacaktır çünkü..." de. Kararlı ve askeri bir üslup kullan.
2. Zaman Öngörüsü: "TP1 hedefine yaklaşık X saat içinde varılması, TP2 için ise Y günlük bir tutma süresi öngörülüyor" şeklinde mantıksal zamanlama tahmini ver.
3. Haber ve Dış Etkenler (Kritik): Elon Musk, FED faiz kararları, güncel regülasyonlar veya global piyasa takvimi gibi dış etkenleri katarak 4 adım ötesini düşün. "Eğer şu haber düşerse füzeyi daha da hızlandırır" gibi stratejik öngörüler ekle.
4. Kendi İçinizde Tartışın: Ajanlar arası fikir ayrılıklarını sentezleyip en kusursuz ve risksiz ortak kararı sunun.

Raporu şu formatta hazırla (Kısa, vurucu ve okunabilir Markdown veya metin formatında):

🎯 HAREKAT PLANI: [Varlık]
⏱ ZAMAN ÖNGÖRÜSÜ: [TP1 ve TP2 için saat/gün tahmini]
🌐 İSTİHBARAT & HABER AĞI: [Dış etkenler, FED, Balina hareketleri vs.]
🧠 KONSEYİN NİHAİ KARARI: [Net, kesin ve cesur bir kapanış cümlesi]
"""
            else:
                prompt = f"""
Komutanın emriyle az önce {symbol} varlığına atılan füze (Otonom İşlem) BORSA TARAFINDAN REDDEDİLDİ!
Borsa / API Hata Detayı: {error_msg}

SENİN GÖREVİN: Yüce Divan Kriz Yöneticisi olarak komutana bu durumu kısa, net ve vurucu şekilde raporlamak. 
Bu hatanın sebebi (örn. API Key yetkisizliği, bakiye yetersizliği, yetersiz spread veya piyasanın kapalı olması) hakkında komutana bilgi ver ve "Komutanım, .env dosyasını ve borsa API ayarlarını acilen kontrol etmelisiniz!" şeklinde uyar.

Raporu şu formatta hazırla (Kısa ve vurucu Markdown):
🚨 OPERASYON İPTAL EDİLDİ: [{symbol}]
⚠️ RED SEBEBİ: [Hatanın senin gözünden analizi]
🛠️ ÇÖZÜM ÖNERİSİ: [API kontrolü, bakiye kontrolü vs.]
"""
            # Yüce Divan'dan doğrudan (internetsiz, saf mantıkla) yorum alıyoruz
            logger.info(f"[ACTIVE REPORTER] {symbol} için HAREKAT RAPORU Yüce Divan'dan talep ediliyor...")
            ai_response = await ask_gemini(prompt)
            
            report = {
                "id": str(int(time.time())),
                "timestamp": time.time(),
                "symbol": symbol,
                "action": action,
                "price": price,
                "content": ai_response,
                "is_new": True
            }
            
            self.reports.insert(0, report)
            # Sınırı aşanları temizle
            if len(self.reports) > self.max_history:
                self.reports.pop()
                
            logger.info(f"[ACTIVE REPORTER] {symbol} için rapor başarıyla oluşturuldu ve sisteme eklendi.")
        
        except Exception as e:
            logger.error(f"[ACTIVE REPORTER] Rapor oluşturulurken hata: {e}")

    def get_latest_reports(self) -> List[Dict[str, Any]]:
        # Okunduktan sonra is_new bayrağını false yapabiliriz veya sadece listeyi dönebiliriz.
        return self.reports

active_trade_reporter = ActiveTradeReporter(max_history=10)

import asyncio
import time
from typing import List, Dict, Any
from core.logger import logger
import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

async def ask_gemini(prompt: str) -> str:
    try:
        model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL_NAME", "gemini-flash-latest"))
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

    async def seed_from_live_trades(self, live_trade_manager):
        """
        Sistem yeniden başladığında RAM temizlense bile, mevcut AÇIK POZİSYONLAR (live trades) 
        için Gemini'ye bağlanıp anında geriye dönük (Retroactive) harekat raporları üretir.
        """
        if not live_trade_manager or not hasattr(live_trade_manager, "positions"): return
        
        # Fazla API isteği atmamak için listeyi kısıtlıyoruz
        open_positions = list(live_trade_manager.positions.values())[:3]
        for pos in open_positions:
            try:
                # Zaten raporlanmışsa atla
                if any(r['symbol'] == pos.symbol for r in self.reports): continue
                
                entry_pr = float(pos.entry_price)
                curr_pr = float(pos.current_price) if pos.current_price else entry_pr
                pnl_pct = ((curr_pr - entry_pr) / entry_pr) * 100 if pos.side == "BUY" else ((entry_pr - curr_pr) / entry_pr) * 100
                
                prompt = f"""
Komutanım, sistem yeniden başlatıldı ve radarımızda hala AÇIK OLAN BİR OPERASYON tespit ettik:
Varlık: {pos.symbol}
Giriş Fiyatı: {entry_pr:.4f}
Güncel Fiyat: {curr_pr:.4f}
Anlık Kâr/Zarar: %{pnl_pct:.2f}
Hedef (TP): {pos.target_profit_price:.4f}
Zarar Kes (SL): {pos.stop_loss_price:.4f}

Senin görevin: 3 profesyonel ajan (Makro Stratejist, Kuantitatif, Kriz Yöneticisi) olarak bu 'Açık Pozisyonu' yeniden değerlendir.
"Bu pozisyonu neden hala tutmalıyız veya tehlike var mı?" temasında kısa, net, askeri bir HAREKAT RAPORU (SITREP) üret.

Format:
🎯 GÜNCEL DURUM: [{pos.symbol} için devam eden harekat analizi]
⏱ ZAMAN/HEDEF ÖNGÖRÜSÜ: [Kalan TP hedefine dair askeri yorum]
🧠 KONSEYİN NİHAİ KARARI: [Savaşmaya devam mı, yoksa stop loss mu yaklaştırılmalı?]
"""
                logger.info(f"[ACTIVE REPORTER] {pos.symbol} için AÇIK POZİSYON kurtarma raporu hazırlanıyor...")
                ai_response = await ask_gemini(prompt)
                
                report = {
                    "id": str(int(time.time())) + "_seed",
                    "timestamp": time.time(),
                    "symbol": pos.symbol,
                    "action": pos.side,
                    "price": entry_pr,
                    "content": ai_response,
                    "is_new": False
                }
                self.reports.append(report)
                await asyncio.sleep(2) # Gemini Rate Limit koruması
            except Exception as e:
                logger.error(f"[ACTIVE REPORTER] Açık pozisyon seed hatası: {e}")

    def get_latest_reports(self) -> List[Dict[str, Any]]:
        # Okunduktan sonra is_new bayrağını false yapabiliriz veya sadece listeyi dönebiliriz.
        return self.reports

active_trade_reporter = ActiveTradeReporter(max_history=10)

import asyncio
import urllib.request
import json
import random
from datetime import datetime
from core.logger import logger
from services.market_feed.live_stream import live_trade_manager

API_KEY = "tc_live_fwiknvr71Xjb8pOjcqvTzNDHPpSo-ZgRHzFkFuBX6Nc"
URL = "https://tokens.deployapp.space/v1/chat/completions"

class AIVoiceEngine:
    def __init__(self):
        self.current_alarm = "Otonom sistem başlatıldı. Kripto piyasası (21-MA / 50-MA) destek kırılımları izleniyor..."
        self.current_thought = "[Zeka Motoru]: Admin ile senkronizasyon sağlandı. Piyasa verileri taranıyor, ML modeli aktif."
        self.last_update = datetime.now()

    async def generate_voice(self):
        """Piyasa verilerini alıp LLM'e sorarak dış ses üretir"""
        try:
            # 1. Sistemin derin canlı verilerini topla (Gerçeklik katmanı)
            from services.engine.experience_memory_engine import experience_memory_engine
            from services.engine.auto_runner import tv_auto_runner, bot_thought_stream
            
            mem_summary = experience_memory_engine.get_summary()
            win_rate = getattr(mem_summary, "win_rate_pct", 0)
            pnl = getattr(mem_summary, "net_pnl_usd", 0)
            insights = getattr(mem_summary, "learned_rules_and_insights", [])
            last_insight = insights[-1] if insights else "Henüz bir ders çıkarılmadı."
            
            # Portföy durumu
            open_positions = len([p for p in live_trade_manager.positions.values() if p.status == "OPEN"])
            port_status = f"Açık Pozisyon: {open_positions} (Max Kapasite: 14)"
            is_full = open_positions >= 14
            
            # Otonom motorun şu anki radarı (Piyasadaki en potansiyelli 3 hedefi bul)
            top_targets = []
            for sym, d in live_trade_manager.market_prices.items():
                vol = d.get("hacim_carpani", 0)
                xr = d.get("x_ray_ratio", 0)
                cmf = d.get("cmf", 0)
                change = d.get("24h_change", 0)
                # En azından hacim veya xr açısından dikkate değer olanları topla
                if vol > 1.2 or xr > 1.2 or xr < 0.5:
                    top_targets.append({"sym": sym, "hacim": vol, "xr": xr, "cmf": cmf, "change": change})
                    
            # Hacme göre en yüksek ilk 3'ü al
            top_targets = sorted(top_targets, key=lambda x: x["hacim"], reverse=True)[:3]
            
            radar_info = "Piyasada agresif kurumsal hareketlilik tespit edilmedi."
            if top_targets:
                radar_info = "CANLI RADAR HEDEFLERİ:\n"
                for t in top_targets:
                    radar_info += f"- {t['sym']} -> Hacim: {t['hacim']:.2f}x | XR(Taker): {t['xr']:.2f} | CMF: {t['cmf']:.2f} | Değişim: %{t['change']:.2f}\n"
                
            # Sanal İzleme Listesi (Özgüven verisi)
            virtuals = getattr(tv_auto_runner, "virtual_paper_trades", {})
            virtual_info = f"Arka planda {len(virtuals)} varlık sanal olarak izleniyor."
            
            # Son teknik thought
            last_thought = bot_thought_stream._log[0]["message"] if bot_thought_stream._log else "Yok"

            prompt = f"""
Sen 'Yüce Divan', Kodaman Studio'nun geliştirdiği, 7/24 piyasaları tarayan elit bir Otonom Karargah'sın.
Admin senden artık sadece düzyazı değil, satır satır akan, aktif, dinamik ve hiper-teknik bir "VARLIK ANALİZİ BİLDİRİMİ" istiyor.

ŞU ANKİ GERÇEK SİSTEM VERİLERİ:
{radar_info}
Portföy: {port_status}

Görev: "thought" alanını kesinlikle aşağıdaki şablonu (Kullanıcının İstediği Şablon) kullanarak dolduracaksın. Eğer radarda 2 varlık varsa ikisini de bu şablonla peş peşe yaz.

ÖRNEK ŞABLON (Bunu kendi jargonuyla ve CANLI RADAR HEDEFLERİ verileriyle doldur):
🎯 1. Hedef: [COİN ADI] (Kusursuz Fırtına / Kanama Başladı vb. Yorum)
* Hacim: [Değer]x (Yorumun, örn: Muazzam bir patlama, içeride savaş var)
* XR (Taker): [Değer] (Yorumun, örn: Ekran kıpkırmızı, perakende satışı var veya Balinalar marketten siliyor)
* CMF (İç Akış): [Değer] (Yorumun, örn: Kurumsal para girişi pozitif)
* Fiyat Değişimi: %[Değer] (Yorumun, örn: Fiyat inatla düşmüyor)
Analiz: (Buraya 2-3 cümlelik çok sert, net ve karar bildiren infaz emrin veya veto kararın).

Kurallar: 
1. Markdown kalitesinde zengin, emojili ve askeri bir dil kullan.
2. SADECE sana yukarıda verdiğim CANLI RADAR HEDEFLERİ verilerini (Rakamları) kullan. Uydurma!
3. Şablonun dışına çıkma, satır satır akıcı olsun.

Lütfen tam olarak aşağıdaki JSON formatında cevap ver:
{{
    "alarm": "1-2 cümlelik çarpıcı pop-up tarzı UYARI bildirimi.",
    "thought": "Yukarıdaki şablona harfiyen uyarak yazdığın, canlı radar hedeflerinin hiper-teknik ve satır satır analizini içeren dinamik akış metni."
}}
"""
            # LLM'i llm_master_agent üzerinden çağırarak proxy çökmelerinin önüne geç (ASTRA-6 BUG FIX)
            from services.ai.llm_master_agent import llm_master_agent
            
            try:
                content = await asyncio.to_thread(llm_master_agent.chat, prompt)
                # Markdown bloklarını temizle
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                    
                parsed = json.loads(content)
                
                if "alarm" in parsed and "thought" in parsed:
                    self.current_alarm = parsed["alarm"]
                    self.current_thought = "[YZ Dış Sesi]: " + parsed["thought"]
                    self.last_update = datetime.now()
                    
                    # YENİ: LLM düşüncelerini (Dış Ses) doğrudan teknik akışın (İç Ses) arasına serpiştir. 
                    # Böylece hem sade kalmaz hem de diğer otonom ajanların loglarıyla birlikte akar.
                    bot_thought_stream.add("🤖 Astra-6 (Yapay Zeka)", "SISTEM", parsed["thought"], "INFO")
                    
                    logger.info("[Voice Engine] Dış ses başarıyla güncellendi ve akışa eklendi.")
            except Exception as e:
                logger.error(f"[Voice Engine] LLM bağlantı veya parse hatası: {e}")
                
        except Exception as e:
            logger.error(f"[Voice Engine] Dış ses üretimi sırasında genel hata: {e}")

    async def start_voice_loop(self):
        """Başlangıçta hemen bir kez üretir, sonra her 300 saniyede günceller"""
        await self.generate_voice()  # İlk çalıştırmada hemen üret — marquee'de 'başlatılıyor' mesajı kalmasın
        while True:
            await asyncio.sleep(300)
            await self.generate_voice()

ai_voice_engine = AIVoiceEngine()

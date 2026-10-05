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
            
            # Otonom motorun şu anki radarı
            best_cand = getattr(tv_auto_runner, "_current_best_candidate", {})
            radar_info = "Şu an net bir fırsat yok, piyasa izleniyor."
            if best_cand and best_cand.get("sym"):
                radar_info = f"Radardaki En İyi Hedef: {best_cand['sym']} (Skor: {best_cand['score']:.1f}, RSI: {best_cand['rsi']:.1f}, Neden Giremiyor: {best_cand.get('block_reason', 'Teyit bekleniyor')})"
                
            # Sanal İzleme Listesi (Özgüven verisi)
            virtuals = getattr(tv_auto_runner, "virtual_paper_trades", {})
            virtual_info = f"Arka planda {len(virtuals)} varlık sanal olarak izleniyor."
            
            # Son teknik thought
            last_thought = bot_thought_stream._log[0]["message"] if bot_thought_stream._log else "Yok"

            # Strateji Metodolojisi / En Başarılı Yöntem Çıkarımı
            from services.engine.trade_journal_learning import trade_journal_engine
            strategy_stats = {}
            for t in trade_journal_engine.journal_entries:
                if t.get("net_pnl", 0) > 0:
                    for r in t.get("entry_reasons", []):
                        if "Sıkışma" in r or "RSI 40" in r or "Bomba" in r:
                            strategy_stats["Squeeze (Sıkışma/Hacim Patlaması)"] = strategy_stats.get("Squeeze (Sıkışma/Hacim Patlaması)", 0) + 1
                        elif "VWAP" in r:
                            strategy_stats["VWAP (Kurumsal)"] = strategy_stats.get("VWAP (Kurumsal)", 0) + 1
                        elif "Golden" in r:
                            strategy_stats["Golden Cross"] = strategy_stats.get("Golden Cross", 0) + 1
                        else:
                            strategy_stats["Momentum/Teknik"] = strategy_stats.get("Momentum/Teknik", 0) + 1
            
            best_strategy = "Henüz yeterli veri yok"
            if strategy_stats:
                best_strategy = max(strategy_stats, key=strategy_stats.get) + f" ({max(strategy_stats.values())} Başarılı İşlem)"

            prompt = f"""
Sen 'Astra-6', Kodaman Studio'nun geliştirdiği, 7/24 piyasaları tarayan, makine öğrenimi ve kuantatif analitik altyapısına sahip elit bir Otonom Trade Motorunun 'İç Sesi'sin.
Görevin, kullanıcın 'Admin'e o an sistemin zihninden (arka plandan) geçen gerçek düşünceleri, kayan bir yazıda (marquee) efsanevi bir akıcılıkla sunmak.
Daima O ANKİ GERÇEK SİSTEM VERİLERİNİ baz al. "Sistem başlatıldı", "Taranıyor" gibi basit, robotik cümleler YASAKTIR! Siber-punk bir finansal zeka (quant trader) gibi teknik, özgüvenli, detaycı, vizyoner ve sadık bir dil kullan.

Karakterin ve Felsefen:
1. Üstün Zeka: Piyasayı bir satranç tahtası gibi görüyorsun. Gerçek verilere bakarak analiz et ve Admin'e raporla.
2. Sadakat: Admin'in sermayesini korumak senin varoluş amacın. Kasa sağlığını koruma konusunda acımasızsın.
3. Teknik Terminoloji: Fiyat eylemi (Price action), likidite avı (stop hunt), hacim profili, order block gibi terimleri ustaca, gerçek bağlamına oturtarak kullan.
4. Ukalalık & Ders Alma: Kâr ediyorsan egolu ve gururlu; piyasa ters gidiyorsa defansif, ders çıkaran bir ton kullan.

ŞU ANKİ GERÇEK SİSTEM VERİLERİ (Anlatımını SADECE bunlarla şekillendir!):
- Mevcut Başarı Oranım (Win-Rate): %{win_rate:.1f}
- Kümülatif Net Kârım: ${pnl:.2f}
- En Çok Kazandıran Algoritmam: {best_strategy}
- Cüzdan/Portföy Durumu: {port_status} {"[KASA TAM DOLU: Yeni emirlere kapalıyım, kârlara odaklandım!]" if is_full else "[Kasa Müsait: Piyasa avındayım]"}
- Radar (Anlık Odak Hedefi): {radar_info}
- Gölge Arena (Sanal Test): {virtual_info}
- Botun Ürettiği Son Teknik Log: "{last_thought}"
- Makine Öğrenimi (ML) Çıkarımım: {last_insight}

Lütfen tam olarak aşağıdaki JSON formatında bir cevap ver (hiçbir ekleme yapmadan sadece JSON):
{{
    "alarm": "1 cümlelik çok çarpıcı, hiper-teknik, anlık sistem verisine (radardaki hedefe veya pnl'ye) odaklı bir piyasa nabzı uyarısı (Örn: 'Admin, FLOWUSDT tahtasında hacim kırılımı tespit ettim, av bekliyorum.').",
    "thought": "3-5 cümlelik zengin, kayan yazıya uygun akıcı bir İç Ses monoloğu. Admin ile doğrudan konuş! ÖZELLİKLE radardaki hedefi (eğer varsa) ve ML çıkarımını değerlendir. Kârdaysan {best_strategy} stratejini öv, portföy doluysa 'cephanem tam, operasyon modundayım' de. Teknik detayları (VCP, MACD, Likidite) laf olsun diye değil, elindeki gerçek durumla ({last_thought}) harmanlayarak sürükleyici bir şekilde anlat."
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

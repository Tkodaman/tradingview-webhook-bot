import threading
import time
from typing import Dict, Any, List
from core.logger import logger
from services.ai.llm_master_agent import llm_master_agent
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from services.intelligence.fear_greed_index import fear_greed_client
from services.engine.macro_fundamental_engine import macro_fundamental_engine

class AIDashboardAdvisor:
    def __init__(self):
        self.cached_opportunity: str = "Otonom Analist verileri topluyor..."
        self.cached_psychology: str = "Piyasa psikolojisi analiz ediliyor..."
        
        self.opp_last_update: float = 0
        self.psy_last_update: float = 0
        self.update_interval: float = 300.0  # 5 dakika
        
        self._lock = threading.Lock()
        
    def _generate_opportunity_bg(self):
        """Top 5 piyasa verisini Astra AI'a atar ve 2 cümlelik avcı analizi ister."""
        try:
            market_data = tradingview_live_client.fetch_live_market_data()
            if not market_data:
                return
            
            # Basit bir momentum skorlaması (RSI + Hacim + CMF)
            scored = []
            for sym, d in market_data.items():
                rsi = float(d.get("rsi") or 50)
                vol = float(d.get("volume_ratio") or 1.0)
                cmf = float(d.get("cmf") or 0.0)
                score = (rsi * 0.5) + (vol * 10) + (cmf * 20)
                scored.append((sym, rsi, vol, cmf, score))
                
            scored.sort(key=lambda x: x[4], reverse=True)
            top5 = scored[:5]
            
            prompt = "Aşağıdaki 5 varlık, sistemin momentum taramasında öne çıktı:\n"
            for s in top5:
                prompt += f"- {s[0]}: RSI={s[1]:.1f}, Vol={s[2]:.1f}x, CMF={s[3]:.2f}\n"
            prompt += "\nLütfen bu 5 varlığa Quant Fon yöneticisi gözüyle bakıp, hangisinin balina alımı veya sağlıklı yükseliş olduğunu en fazla 2 cümleyle özetle. (Örn: 'BTC ve ETH güçlü ama LINK'teki CMF uyuşmazlığı birikime işaret ediyor.')"
            
            if getattr(llm_master_agent, "_ready", False):
                response = llm_master_agent.chat(prompt)
                with self._lock:
                    self.cached_opportunity = response
            else:
                # LLM hazır değilse (API Key yoksa) deterministik fırsat analizi
                with self._lock:
                    if len(top5) > 0:
                        best = top5[0]
                        self.cached_opportunity = f"Otonom tarama sonucunda lider fırsat {best[0]} (RSI: {best[1]:.1f}). Hacim ({best[2]:.1f}x) profili değerlendiriliyor. Kusursuz bir Golden Setup oluşumu bekleniyor."
                    else:
                        self.cached_opportunity = "Şu an piyasada kayda değer güçlü bir momentum (fırsat) dalgası görülmüyor, beklemedeyiz."
                    
        except Exception as e:
            logger.error(f"Opportunity AI Error: {e}")
        finally:
            self.opp_last_update = time.time()

    def _generate_psychology_bg(self):
        """Korku Endeksi ve Makro Karartma Kalkanı verisini birleştirip sentez yapar."""
        try:
            fg = fear_greed_client.get_assessment()
            blackout_active, blackout_reason = macro_fundamental_engine.is_blackout_window_active()
            
            prompt = f"Piyasa Korku & Açgözlülük: {fg.value} ({fg.sentiment}).\n"
            if blackout_active:
                prompt += f"Şu an MAKRO KARARTMA devrede: {blackout_reason}\n"
            else:
                prompt += "Makro takvim sakin, veri şoku beklenmiyor.\n"
                
            prompt += "\nLütfen bir Wall Street risk yöneticisi gibi en fazla 2 cümleyle mevcut piyasa psikolojisini ve botun şu an alması gereken gardı özetle. (Örn: 'Piyasa aşırı açgözlü ve FED kararı yaklaşıyor. Yeni alımları durdurup defansif moda geçiyorum.')"
            
            if getattr(llm_master_agent, "_ready", False):
                response = llm_master_agent.chat(prompt)
                with self._lock:
                    self.cached_psychology = response
            else:
                # LLM hazır değilse (API Key yoksa) deterministik ama dinamik bir sentez üret
                with self._lock:
                    if blackout_active:
                        self.cached_psychology = f"⚠️ MAKRO KARARTMA AKTİF: {blackout_reason}. Piyasa aşırı riskli. Otonom bot yeni alımları tamamen durdurdu ve sadece açık işlemleri koruyor."
                    else:
                        if fg.value < 30:
                            self.cached_psychology = f"Piyasa Aşırı Korku seviyesinde ({fg.value}). Otonom motor bu paniği bir dip fırsatı olarak değerlendiriyor; keskin dönüş yakalamak için izlemede."
                        elif fg.value > 75:
                            self.cached_psychology = f"Piyasada Aşırı Açgözlülük ({fg.value}) hakim. Otonom motor FOMO'ya kapılmıyor, yeni alımlar riskli görüldüğü için kâr-al (Take-Profit) hedeflerine odaklanıyoruz."
                        else:
                            self.cached_psychology = f"Piyasa Nötr/Dengeli ({fg.value}). Makro takvim sakin. Otonom motor standart strateji rejiminde, teknik sinyallere sadık kalarak güvenli avlanıyor."
                    
        except Exception as e:
            logger.error(f"Psychology AI Error: {e}")
        finally:
            self.psy_last_update = time.time()

    def _generate_correlation_bg(self):
        """Korelasyon ısı haritası üzerinden risk (Double Exposure) sentezi yapar."""
        try:
            from services.market_feed.live_stream import live_trade_manager
            from services.risk_engine.expert_analytics import expert_analytics_engine
            
            corr_data = expert_analytics_engine.get_correlation_heatmap(live_trade_manager.positions)
            
            if corr_data.get("status") == "OK":
                prompt = "Şu an açık olan pozisyonlarımızın Pearson korelasyon matrisi:\n"
                for a, b_dict in corr_data.get("matrix", {}).items():
                    for b, val in b_dict.items():
                        if a != b:
                            prompt += f"{a} - {b}: {val}\n"
                    
                prompt += "\nLütfen bir Risk Yöneticisi gözüyle bu matrisi incele. 0.85 üzeri korelasyonlar 'Double Exposure' (Çifte Risk) taşır. En fazla 2 cümleyle risk durumumuzu özetle ve hangi piyasadan yeni işlem almamız gerektiğini otonom olarak tavsiye et."
                
                if getattr(llm_master_agent, "_ready", False):
                    response = llm_master_agent.chat(prompt)
                    with self._lock:
                        self.cached_correlation = response
                else:
                    with self._lock:
                        warnings = corr_data.get("warnings", [])
                        if warnings:
                            self.cached_correlation = f"Çifte Risk Tespit Edildi: {warnings[0]}"
                        else:
                            self.cached_correlation = "Mevcut pozisyonlar arası risk dağılımı sağlıklı. Çifte riske yakalanmadan portföy çeşitliliği korunuyor."
            else:
                # Pozisyon yoksa veya sadece 1 tane varsa (Korelasyon için en az 2 gerekir)
                open_pos_count = len([p for p in live_trade_manager.positions.values() if getattr(p, "status", "OPEN") == "OPEN"])
                
                if open_pos_count == 1:
                    single_sym = [p for p in live_trade_manager.positions.values() if getattr(p, "status", "OPEN") == "OPEN"][0].symbol
                    msg = f"Şu an portföyde sadece {single_sym} pozisyonu aktif. Çifte risk (Double Exposure) korelasyonu hesaplanabilmesi için en az 2 farklı pozisyon gereklidir. Otonom motor yeni fırsatları tarıyor."
                    with self._lock:
                        self.cached_correlation = msg
                else:
                    prices = live_trade_manager.market_prices
                    if prices:
                        # En yüksek hacim/skor lu 5 varlığı bul
                        sorted_symbols = sorted(prices.keys(), key=lambda k: prices[k].get("volume_ratio", 1.0) or 1.0, reverse=True)[:5]
                        sym_list = ", ".join(sorted_symbols)
                        fallback_msg = f"Şu an aktif pozisyonumuz bulunmuyor. Otonom motor; piyasadaki hacim patlaması yaşayan {sym_list} varlıklarını yakın takibe aldı. Sektörel çifte riske (Double Exposure) yakalanmamak için giriş fırsatları filtreleniyor."
                        with self._lock:
                            self.cached_correlation = fallback_msg
                    else:
                        with self._lock:
                            self.cached_correlation = "Astra AI: Piyasada izlenen varlık bulunmuyor veya tarama henüz başlamadı."
                        
        except Exception as e:
            logger.error(f"Correlation AI Error: {e}")
        finally:
            self.cor_last_update = time.time()

    def get_opportunity_analysis(self) -> str:
        now = time.time()
        if now - self.opp_last_update > self.update_interval:
            self.opp_last_update = now
            threading.Thread(target=self._generate_opportunity_bg, daemon=True).start()
        return self.cached_opportunity

    def get_psychology_synthesis(self) -> str:
        now = time.time()
        if now - self.psy_last_update > self.update_interval:
            self.psy_last_update = now
            threading.Thread(target=self._generate_psychology_bg, daemon=True).start()
        return self.cached_psychology
        
    def get_correlation_synthesis(self) -> str:
        now = time.time()
        if now - getattr(self, "cor_last_update", 0) > self.update_interval:
            self.cor_last_update = now
            threading.Thread(target=self._generate_correlation_bg, daemon=True).start()
        return getattr(self, "cached_correlation", "Korelasyon analizi yapılıyor...")

ai_dashboard_advisor = AIDashboardAdvisor()

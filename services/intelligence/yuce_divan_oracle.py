import time
import random
from typing import Dict, Any

class YuceDivanOracle:
    """
    7'li Yüce Divan (Konsey) Karar Motoru.
    Botun Kantitatif (Teknik) filtresinden geçen işlemlere 'Nihai Onay' veya 'VETO' verir.
    Roller: İstihbarat, Savcı, Kantitatif, Gölge Avcısı, Makro-Stratejist, Keskin Nişancı, Kriz Mühendisi.
    """
    def __init__(self):
        self.decision_cache = {}
        self.CACHE_TTL = 300  # 5 dakika önbellek (Sistemi yormamak için)

    async def get_council_decision(self, symbol: str, current_score: float, rsi: float, volume_ratio: float) -> Dict[str, Any]:
        """
        Gelen parametrelere göre 7'li Divan'ın sentez kararını döndürür.
        """
        now = time.time()
        # Cache (Donukluğu / Performans yorgunluğunu önleme)
        if symbol in self.decision_cache:
            cache_entry = self.decision_cache[symbol]
            if now - cache_entry['timestamp'] < self.CACHE_TTL:
                return cache_entry['result']

        # SİMÜLE EDİLMİŞ 7'Lİ DİVAN SENTEZİ (Otonom Heuristic)
        approved = True
        veto_reason = ""
        veto_agent = ""
        
        # 1. Savcı İncelemesi (Aşırı Şişme veya Tuzak)
        if rsi > 75:
            approved = False
            veto_agent = "⚖️ Yüce Divan Savcısı"
            veto_reason = f"RSI {rsi:.1f} çok şişik, bu bir Boğa Tuzağı (Bull Trap) olabilir!"
            
        # 2. Makro Stratejist & Gölge Avcısı İncelemesi (Hacimsiz Yükseliş)
        elif volume_ratio < 0.8:
            approved = False
            veto_agent = "♟️ Gölge Avcısı"
            veto_reason = f"Hacim çok cılız ({volume_ratio:.2fx}). Karanlık Havuzda para girişi teyidi YOK!"
            
        # 3. Kriz Mühendisi İncelemesi (Bıçak Yakalama)
        elif rsi < 30 and current_score < 60:
            approved = False
            veto_agent = "☣️ Kriz Mühendisi"
            veto_reason = "Bıçak düşüyor! Stress testi negatif, bu seviyeden dönme ihtimali bütçeyi tehdit eder."

        if approved:
            admin_msg = f"Komutanım, {symbol} için 7'li Konsey [ONAY] verdi! 🎯 Keskin Nişancı füzeyi ateşliyor (Skor: {current_score:.1f})"
        else:
            admin_msg = f"Komutanım, {symbol} İNFAZI İPTAL! {veto_agent} VETO etti: {veto_reason}"

        result = {
            "approved": approved,
            "admin_msg": admin_msg
        }
        
        self.decision_cache[symbol] = {
            "timestamp": now,
            "result": result
        }
        
        return result

yuce_divan = YuceDivanOracle()

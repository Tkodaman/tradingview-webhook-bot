import math
from typing import Dict, Any, List
from core.logger import logger

class KellyEngine:
    """
    Tier-1 Yükseltmesi: Dinamik "Kelly Kriteri" ve Bileşik Kâr (Re-Balans) Motoru.
    Geçmiş işlem performansına ve anlık win rate'e (Kazanma Oranı) bakarak,
    sermaye koruması ve agresif büyüme arasındaki mükemmel dengeyi hesaplar.
    """
    def __init__(self):
        self.default_win_rate = 0.55
        self.default_reward_risk = 2.0
        self.fraction = 0.5  # Half-Kelly (Daha güvenli, volatility'i azaltır)
        self.max_allocation_pct = 0.20  # Bir işleme kasanın max %20'si
        self.min_allocation_pct = 0.05  # En az %5

    def calculate_allocation_pct(self, recent_trades: List[Dict[str, Any]] = None, ai_score: float = 0.0) -> float:
        """
        Geçmiş işlemlere göre kazanma oranını hesaplar ve Kelly Formülü ile
        kasadan yatırılacak ideal yüzdeyi döner.
        
        Args:
            recent_trades: Son kapanan işlemler (Win/Loss durumu için)
            ai_score: İşleme girerken yapay zekanın güven skoru (0-100 veya 0-10)
        """
        win_rate = self.default_win_rate
        reward_risk = self.default_reward_risk
        
        # Son işlemlere göre dinamik hesaplama (Geçmiş veri varsa)
        if recent_trades and len(recent_trades) >= 5:
            wins = sum(1 for t in recent_trades if t.get('pnl', 0) > 0)
            losses = len(recent_trades) - wins
            
            # Güncel win rate (Son 20-50 işlem)
            win_rate = wins / len(recent_trades)
            
            # Ortalama R/R (Risk Ödül) hesaplama
            avg_win = sum(t.get('pnl', 0) for t in recent_trades if t.get('pnl', 0) > 0) / max(1, wins)
            avg_loss = abs(sum(t.get('pnl', 0) for t in recent_trades if t.get('pnl', 0) < 0) / max(1, losses))
            
            if avg_loss > 0:
                reward_risk = avg_win / avg_loss

        # Hot Streak / Cold Streak Kontrolü
        if win_rate < 0.35:
            logger.warning("📉 [KELLY ENGINE] Soğuk seri (Cold Streak) algılandı. Risk minimize ediliyor.")
            return self.min_allocation_pct
            
        if win_rate > 0.75:
            logger.info("🔥 [KELLY ENGINE] Sıcak seri (Hot Streak) algılandı. Bileşik büyüme agresifleştiriliyor!")
            
        # AI Skoru yüksekse kazanma ihtimalini teorik olarak artır
        # (Örn: AI skoru 10 üzerinden 9 ise win_rate'e ufak bir bonus ekle)
        ai_bonus = 0.0
        if ai_score >= 8.0:
            ai_bonus = 0.05
        elif ai_score <= 4.0:
            ai_bonus = -0.05
            
        adjusted_win_rate = min(0.90, max(0.20, win_rate + ai_bonus))
        
        # Kelly Formula: f* = (p * (b + 1) - 1) / b
        # p: kazanma olasılığı, b: risk-ödül oranı (net odds)
        if reward_risk <= 0:
            return self.min_allocation_pct
            
        f_star = (adjusted_win_rate * (reward_risk + 1) - 1) / reward_risk
        
        # Negatif Kelly çıkarsa (İstatistiksel olarak zarardaysak) minimuma dön
        if f_star <= 0:
            return self.min_allocation_pct
            
        # Half-Kelly ile riski böl (Daha yumuşak bir PnL eğrisi için)
        allocation = f_star * self.fraction
        
        # Sınırları uygula
        final_allocation = min(max(allocation, self.min_allocation_pct), self.max_allocation_pct)
        return round(final_allocation, 3)

kelly_engine = KellyEngine()

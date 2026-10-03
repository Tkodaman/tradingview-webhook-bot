import math
from typing import List, Dict, Any
from core.logger import logger

class KellyCriterionEngine:
    """
    Tier-1 Quant Fon Seviyesi: Dinamik Sermaye ve Risk Yönetimi
    Formül: K = W - ((1 - W) / R)
    W = Kazanma Oranı (Win Rate)
    R = Ortalama Risk/Ödül Oranı (Avg Win / Avg Loss)
    """
    
    def __init__(self):
        self.max_kelly_fraction = 0.5  # Asla kasanın yarısından fazlasını riske etme (Half-Kelly)
        self.min_kelly_fraction = 0.05 # Kayıp serisinde hayatta kalma (Survival) modu
        
    def calculate_multiplier(self, trade_history: List[Dict[str, Any]]) -> float:
        if not trade_history or len(trade_history) < 5:
            return 1.0  # Yeterli veri yoksa nötr çarpan
            
        # ADL (Auto-Deleveraging) Intraday Drawdown Soğutması
        recent_3 = trade_history[-3:]
        if len(recent_3) == 3 and all(float(t.get("net_pnl", 0.0)) < 0 for t in recent_3):
            logger.error("[ADL DEVRE KESİCİ] Üst üste 3 zarar! Sistem Soğutma Modunda (Cooldown). İntikam işlemi kalkanı devrede. Lot Çarpanı: 0.25x")
            return 0.25
            
        wins = 0
        losses = 0
        total_win_pnl = 0.0
        total_loss_pnl = 0.0
        
        for trade in trade_history[-30:]:  # Sadece son 30 işlemi baz al (Rejim değişimi)
            pnl = float(trade.get("net_pnl", 0.0))
            if pnl > 0:
                wins += 1
                total_win_pnl += pnl
            elif pnl < 0:
                losses += 1
                total_loss_pnl += abs(pnl)
                
        total_trades = wins + losses
        if total_trades == 0:
            return 1.0
            
        win_rate = wins / total_trades
        
        avg_win = (total_win_pnl / wins) if wins > 0 else 0.0
        avg_loss = (total_loss_pnl / losses) if losses > 0 else 1.0  # Sıfıra bölmeyi engelle
        
        # Risk / Reward Oranı
        if avg_loss == 0.0:
            r_ratio = 2.0
        else:
            r_ratio = avg_win / avg_loss
            
        # Kelly Kriteri Formülü
        if r_ratio == 0:
            kelly_pct = 0.0
        else:
            kelly_pct = win_rate - ((1.0 - win_rate) / r_ratio)
            
        # Kısıtlamalar (Drawdown Koruması)
        if kelly_pct <= 0:
            logger.warning(f"[KELLY KRİTERİ] Negatif Değer ({kelly_pct:.2f}). Kazanma Oranı: %{win_rate*100:.1f}. DEFANS MODU Aktif.")
            return 0.3  # Bütçeyi %70 küçült
            
        # Agresiflik Çarpanına Çevirme
        # Eğer Kelly 0.20 ise bütçeyi x1.2 büyüt. Kelly 0.5 ise x1.5 büyüt.
        # Maksimum Half-Kelly sınırına takılır.
        safe_kelly = min(kelly_pct, self.max_kelly_fraction)
        safe_kelly = max(safe_kelly, self.min_kelly_fraction)
        
        multiplier = 1.0 + safe_kelly
        
        logger.info(f"[KELLY KRİTERİ] W:{win_rate*100:.1f}% | R:R:{r_ratio:.2f} | K:{kelly_pct:.3f} => Lot Çarpanı: {multiplier:.2f}x")
        
        return round(multiplier, 2)

kelly_engine = KellyCriterionEngine()

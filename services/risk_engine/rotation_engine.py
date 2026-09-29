from typing import Dict, Any, List, Optional
import time

class OpportunityRotationEngine:
    """
    Otonom Rotasyon Motoru (Fırsat Maliyeti Yöneticisi)
    Amacı: Kasa dolu olduğunda veya dışarıda devasa bir fırsat belirdiğinde,
    içerideki en zayıf/doymuş varlığı kapatıp yeni varlığa geçiş kararı almaktır.
    """
    
    def __init__(self):
        self.PORTFOLIO_LIMIT = 5 # Maksimum tutulacak varlık sayısı
        self.MIN_SCORE_GAP_FOR_ROTATION = 8 # Yeni varlığın eskiden en az 8 puan üstün olması gerekir
        self.MIN_VOLUME_FOR_ROTATION = 1.5 # Yeni varlıkta en az 1.5x hacim patlaması olmalı
        
    def evaluate_rotation(self, new_symbol: str, new_score: int, new_data: Dict[str, Any], active_positions: List[Any]) -> Dict[str, Any]:
        """
        Dışarıdaki yeni bir fırsat (new_symbol) için rotasyon (değiştirme) yapılıp yapılmayacağını hesaplar.
        """
        new_vol = new_data.get("volume_ratio", 0.0)
        
        # 1. Aşama: Yeni Varlık Rotasyona Değer mi? (Sentinel Guard)
        if new_vol < self.MIN_VOLUME_FOR_ROTATION:
            return {"rotate": False, "reason": f"Yeni varlık ({new_symbol}) hacmi yetersiz ({new_vol}x). Rotasyon riskine değmez."}
            
        if len(active_positions) < self.PORTFOLIO_LIMIT:
            # Kasa dolmamış, rotasyona gerek yok, direkt alınabilir
            return {"rotate": False, "reason": "Kasa henüz dolmamış, doğrudan alım yapılabilir."}
            
        # 2. Aşama: İçerideki En Zayıf Halkayı Bul (Quant & Risk Guard)
        # İçerideki pozisyonları değerlendir
        weakest_position = None
        weakest_score = 999
        
        for pos in active_positions:
            # Puanlamayı simüle et (Burada pos'un canlı verisine göre gerçek bir puan hesaplanabilir,
            # ancak biz basitleştirmek için PnL durumuna bakıyoruz)
            pnl_pct = getattr(pos, 'unrealized_pnl_pct', 0.0)
            
            # Eğer varlık çok kârda ise (+%5 üzeri) doygunluğa ulaşmış olabilir, rotasyona uygundur (Take Profit)
            # Eğer varlık ekside ise ve uzun süredir hareket etmiyorsa (Ölü Toprak), kesilmeye uygundur
            
            pos_score = 10 # Temel puan
            if pnl_pct > 5.0:
                pos_score -= 5 # Kâr doygunluğu (Kesilmesi kolay)
            elif pnl_pct < 0.0:
                pos_score -= 2 # Zararda olan (Kanayan)
                
            if pos_score < weakest_score:
                weakest_score = pos_score
                weakest_position = pos
                
        if not weakest_position:
            return {"rotate": False, "reason": "Değerlendirilecek aktif pozisyon bulunamadı."}
            
        # 3. Aşama: Olasılık Matrisini Çarpıştır (Cross-Probability)
        if (new_score - weakest_score) >= self.MIN_SCORE_GAP_FOR_ROTATION:
            # Rotasyon Kararı ONAYLANDI
            weak_sym = getattr(weakest_position, 'symbol', "Bilinmiyor")
            return {
                "rotate": True,
                "target_to_close": weak_sym,
                "target_to_open": new_symbol,
                "reason": f"[TAM OTONOM ROTASYON]: {new_symbol} (Skor: {new_score}, Hacim: {new_vol}x) devasa bir fırsat sundu. İçerideki zayıf {weak_sym} varlığı satılarak kaynak bu tarafa aktarılmalıdır."
            }
            
        return {"rotate": False, "reason": f"Puan farkı ({new_score} vs {weakest_score}) rotasyon riskini göze alacak kadar yüksek değil."}

rotation_engine = OpportunityRotationEngine()

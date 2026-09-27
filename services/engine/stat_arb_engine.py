import logging
import numpy as np
from typing import List, Dict, Any

logger = logging.getLogger("StatArbEngine")

class StatisticalArbitrageEngine:
    """
    Koz 2: Statistical Arbitrage & Cointegration Engine (Piyasa-Nötr Motor)
    Yön tahmini (LONG/SHORT) yapmaz, iki korele varlık arasındaki (örn: BTC/ETH) 
    matematiksel makasın (Z-Score) kopuşunu arar.
    Makas koptuğunda pahalıyı açığa satar, ucuzu alır. Risk sıfıra yakındır, cüretkârdır.
    """
    def __init__(self):
        self.pairs_memory: Dict[str, Any] = {}
        self.z_score_threshold = 2.5 # Z-Score 2.5'i aşarsa cüretkar giriş yap.
        self.mean_reversion_threshold = 0.5 # 0.5'e dönerse kâr al ve çık.
        logger.info("[STAT-ARB] Statistical Arbitrage (Piyasa-Nötr) Motoru Aktifleştirildi.")

    def calculate_z_score(self, asset_a_prices: List[float], asset_b_prices: List[float]) -> float:
        """İki varlık fiyatı arasındaki spread'in Z-Skorunu hesaplar."""
        if len(asset_a_prices) < 30 or len(asset_b_prices) < 30:
            return 0.0
            
        spread = np.array(asset_a_prices) - np.array(asset_b_prices)
        mean_spread = np.mean(spread)
        std_spread = np.std(spread)
        
        if std_spread == 0:
            return 0.0
            
        current_spread = spread[-1]
        z_score = (current_spread - mean_spread) / std_spread
        return round(float(z_score), 3)

    def scan_for_opportunities(self, pairs_data: Dict[str, Dict[str, List[float]]]) -> List[Dict[str, Any]]:
        """
        Gelen çiftleri (Örn: {"BTC-ETH": {"A": [...], "B": [...]}}) tarar.
        Z-Score > 2.5 ise "A'yı Sat, B'yi Al", Z-Score < -2.5 ise "A'yı Al, B'yi Sat"
        cüretkar emirlerini üretir.
        """
        opportunities = []
        for pair_name, data in pairs_data.items():
            z = self.calculate_z_score(data["A"], data["B"])
            
            if z >= self.z_score_threshold:
                opportunities.append({
                    "pair": pair_name,
                    "z_score": z,
                    "action": "SHORT_A_LONG_B",
                    "confidence": "HIGH (Over-extended)",
                    "urgency": "IMMEDIATE"
                })
                logger.warning(f"[STAT-ARB] FIRSAT YAKALANDI: {pair_name} | Z-Score: {z} (Aşırı Pahalı, A'yı Sat B'yi Al)")
                
            elif z <= -self.z_score_threshold:
                opportunities.append({
                    "pair": pair_name,
                    "z_score": z,
                    "action": "LONG_A_SHORT_B",
                    "confidence": "HIGH (Over-extended)",
                    "urgency": "IMMEDIATE"
                })
                logger.warning(f"[STAT-ARB] FIRSAT YAKALANDI: {pair_name} | Z-Score: {z} (Aşırı Ucuz, A'yı Al B'yi Sat)")
                
        return opportunities

stat_arb_engine = StatisticalArbitrageEngine()

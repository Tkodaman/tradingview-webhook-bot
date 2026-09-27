import logging
from typing import Dict, Any

logger = logging.getLogger("InsiderFeed")

class CorporateInsiderTracker:
    def __init__(self):
        # Gerçek bir API'ye bağlanana kadar simülasyon modunda değil, tamamen kapalı ve NÖTR döner.
        self.simulation_mode = False

    def fetch_insider_transactions(self, symbol: str) -> Dict[str, Any]:
        """
        Belirtilen varlık için son güncel Corporate Insider işlemlerini döndürür.
        NOT: Gerçek veri akışı bağlanana kadar SAHTE (fake) veri ÜRETMEMEK için daima NÖTR döner.
        """
        # TODO: Gerçek bir API (Örn: Finnhub, SEC EDGAR) bağlandığında buraya eklenecektir.
        
        return {
            "symbol": symbol,
            "has_insider_activity": False,
            "signal_type": "NEUTRAL",
            "net_volume": 0,
            "confidence_modifier": 0.0,
            "qty_multiplier": 1.0,
            "message": "Gerçek insider/on-chain API bağlı değil. (Sahte sinyal üretimi devre dışı)"
        }

insider_tracker = CorporateInsiderTracker()

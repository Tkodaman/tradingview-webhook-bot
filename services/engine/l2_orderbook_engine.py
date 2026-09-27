import logging
import asyncio
from typing import Dict, Any, List

logger = logging.getLogger("L2OrderBookEngine")

class L2OrderBookEngine:
    """
    Koz 3: L2 Emir Defteri (Order Book) ve Spoofing Avcısı
    Derinlik verilerini (Bid/Ask Imbalance) okuyarak balinaların sahte alış/satış duvarlarını 
    (Spoofing) tespit eder. Sadece kritik dengesizlik anlarında tetiklenir (Event-Driven), 
    böylece ana döngüyü yormaz.
    """
    def __init__(self):
        self.imbalance_threshold = 0.85 # %85 ve üzeri dengesizlik cüretkâr bir sinyaldir
        self.is_active = True
        logger.info("[L2-ENGINE] L2 Emir Defteri Micro-Structure Motoru Aktif (Non-Blocking).")

    async def analyze_depth_async(self, symbol: str, bids: List[List[float]], asks: List[List[float]]) -> Dict[str, Any]:
        """
        Asenkron çalışır (Ana sistemi kitlemez).
        bids/asks formatı: [[price, volume], ...]
        """
        if not bids or not asks:
            return {"status": "NO_DATA"}

        total_bid_vol = sum([vol for price, vol in bids])
        total_ask_vol = sum([vol for price, vol in asks])
        
        total_vol = total_bid_vol + total_ask_vol
        if total_vol == 0:
            return {"status": "NO_VOLUME"}

        bid_ratio = total_bid_vol / total_vol
        ask_ratio = total_ask_vol / total_vol

        # Spoofing Tespiti & Fırsat Çıktısı
        opportunity = None
        if bid_ratio > self.imbalance_threshold:
            # Aşırı alış duvarı var. Bu gerçek mi yoksa spoofing mi?
            # Cüretkâr Ajan: Balina sahte duvar koyduysa fiyatı yukarı sürecektir.
            opportunity = {
                "symbol": symbol,
                "signal": "BUY_SPOOF_DETECTED",
                "imbalance": round(bid_ratio * 100, 2),
                "action": "AGGRESSIVE_LONG",
                "urgency": "MILLISECOND"
            }
            logger.warning(f"[L2-ENGINE] {symbol} tahtasında %{round(bid_ratio*100, 1)} Alış Baskısı! (Olası Spoofing, LONG Tetikleniyor)")

        elif ask_ratio > self.imbalance_threshold:
            opportunity = {
                "symbol": symbol,
                "signal": "SELL_SPOOF_DETECTED",
                "imbalance": round(ask_ratio * 100, 2),
                "action": "AGGRESSIVE_SHORT",
                "urgency": "MILLISECOND"
            }
            logger.warning(f"[L2-ENGINE] {symbol} tahtasında %{round(ask_ratio*100, 1)} Satış Duvarı! (Olası Spoofing, SHORT Tetikleniyor)")

        return {
            "status": "ANALYZED",
            "imbalance_metrics": {"bid_ratio": bid_ratio, "ask_ratio": ask_ratio},
            "opportunity": opportunity
        }

l2_orderbook_engine = L2OrderBookEngine()

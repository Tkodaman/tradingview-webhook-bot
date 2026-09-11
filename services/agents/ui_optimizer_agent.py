import time
from typing import Dict, Any

from routers.top_picks_cache import get_cached_top_picks
from services.engine.market_advisory_tracker import market_advisory_tracker
from services.market_feed.live_stream import live_trade_manager
from services.engine.trade_journal_learning import trade_journal_engine

class UIOptimizerAgent:
    """
    Tüm dashboard verilerini saniyesinde tek bir pakette birleştirerek (Unified State) 
    görsel çakılmaları ve titremeleri engelleyen ara katman ajanı.
    """
    def __init__(self):
        pass

    def get_unified_state(self) -> Dict[str, Any]:
        """
        Dashboard'un ihtiyaç duyduğu tüm verileri (Pozisyonlar, Haberler, Tarama Listesi, vs.)
        tek bir JSON'da birleştirip döner. Asla dış API (ağ) beklemesi yapmaz, RAM'deki veriyi verir.
        """
        # 1. Aktif Pozisyonlar
        try:
            positions = live_trade_manager.get_active_positions()
        except Exception:
            positions = []
            
        # 2. Market Advisory Streams (Kayan Yazı Verileri)
        try:
            advisory_streams = market_advisory_tracker.get_streams()
        except Exception:
            advisory_streams = {"CRYPTO": [], "NASDAQ": [], "BIST": []}
            
        # 3. Top Actionable Picks (Tarama Listesi)
        try:
            picks = get_cached_top_picks()
            picks = sorted(picks, key=lambda x: x.get("confidence_pct", 0), reverse=True)[:100]
        except Exception:
            picks = []
            
        # 4. Market Pulse Data (Risk Parametreleri vb.)
        try:
            pulse = live_trade_manager.get_market_pulse()
        except Exception:
            pulse = {}
            
        # 5. Trade Geçmişi Özeti
        try:
            journal = trade_journal_engine.get_journal()
            closed = [t for t in journal if t.get("exit_time")]
            recent_closed = sorted(closed, key=lambda x: x.get("exit_time", ""), reverse=True)[:10]
        except Exception:
            recent_closed = []
            
        return {
            "status": "success",
            "timestamp": time.time(),
            "active_positions": positions,
            "advisory_streams": advisory_streams,
            "top_picks": picks,
            "market_pulse": pulse,
            "recent_trades": recent_closed
        }

ui_optimizer_agent = UIOptimizerAgent()

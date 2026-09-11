import time
from copy import deepcopy
from typing import Dict, Any, Optional

from services.agents.ui_optimizer_agent import ui_optimizer_agent
from core.logger import logger

class DataFlowAuditorAgent:
    """
    Dashboard veri akışını optimize eden, sadece değişen (Delta) verileri
    zaman damgası ile paketleyen Olay Güdümlü denetleyici ajan.
    """
    def __init__(self):
        self._last_state: Optional[Dict[str, Any]] = None
        self._last_hash: Optional[str] = None
        
    def get_audited_delta(self) -> Optional[Dict[str, Any]]:
        """
        Sistemin o anki durumunu çeker. Bir önceki duruma göre fark var mı bakar.
        Fark varsa zaman damgası ekleyip gönderir. Yoksa None döner (Veri çöpünü önler).
        """
        try:
            current_state = ui_optimizer_agent.get_unified_state()
        except Exception as e:
            logger.error(f"UI Optimizer Agent hatası: {e}")
            return None
            
        state_to_compare = deepcopy(current_state)
        if "timestamp" in state_to_compare:
            del state_to_compare["timestamp"]
            
        # Hafif parmak izi (Fingerprint) - tam JSON serileştirme yerine kritik alanlardan hash
        try:
            positions_fp = str([(p.get("symbol"), p.get("current_price"), p.get("unrealized_pnl")) 
                                 for p in current_state.get("active_positions", [])])
            picks_fp = str([(p.get("symbol"), p.get("confidence_pct"), p.get("price")) 
                            for p in current_state.get("top_picks", [])[:10]])  # Sadece ilk 10
            advisory_fp = str({k: v[:2] for k, v in current_state.get("advisory_streams", {}).items()})
            current_hash = f"{positions_fp}|{picks_fp}|{advisory_fp}"
        except Exception:
            current_hash = str(time.time())  # Hata durumunda her zaman güncelle
        
        if self._last_hash == current_hash:
            # Hiçbir veri değişikliği yok, arayüze veri basma!
            return None
            
        # Değişim var
        self._last_hash = current_hash
        self._last_state = deepcopy(current_state)
        
        # Milisaniye hassasiyetli zaman damgası
        current_state["timestamp_ms"] = int(time.time() * 1000)
        
        return current_state

data_flow_auditor_agent = DataFlowAuditorAgent()

import time
from services.agents.data_analysis_agent import data_analysis_agent

_cache = {"time": 0, "data": []}

def get_cached_top_picks():
    now = time.time()
    if now - _cache["time"] > 20:  # Cache for 20 seconds (Daha sık veri tazelemesi)
        try:
            picks = data_analysis_agent.top_picks()
            _cache["data"] = picks.get("picks", []) if isinstance(picks, dict) else picks
            _cache["time"] = now
        except Exception as e:
            pass
    return _cache["data"]

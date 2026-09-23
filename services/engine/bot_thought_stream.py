"""
Bot Dusunce Akisi (Bot Thought Stream)
Fakeout Guard, Stop-Hunt Evader ve Korelasyon Filtresi gibi risk motorlarinin
"neden bekliyorum / neden koruyorum" kararlarini canli bir akis olarak tutar.
Sadece bellek ici, hafif bir ring-buffer'dir; harici bagimlilik veya ag cagrisi yoktur.
"""
from collections import deque
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List

TRT = ZoneInfo("Europe/Istanbul")
MAX_THOUGHTS = 100


class BotThoughtStream:
    def __init__(self):
        self._log: deque = deque(maxlen=MAX_THOUGHTS)

    def add(self, category: str, symbol: str, message: str, level: str = "INFO"):
        self._log.appendleft({
            "timestamp": datetime.now(TRT).strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "symbol": symbol,
            "message": message,
            "level": level,
        })

    def get_recent(self, limit: int = 30) -> List[Dict[str, Any]]:
        return list(self._log)[:limit]


bot_thought_stream = BotThoughtStream()

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
import time
import uuid

TRT = ZoneInfo("Europe/Istanbul")
MAX_THOUGHTS = 250


class BotThoughtStream:
    def __init__(self):
        self._log: deque = deque(maxlen=MAX_THOUGHTS)
        self._last_seen: Dict[str, float] = {}

    def add(self, category: str, symbol: str, message: str, level: str = "INFO"):
        # TOXIC FILTER / SPAM KESİCİ (Kesin Çözüm)
        # LLM veya diğer tarayıcılar tarafından "HYPERFDUSD" gibi stablecoin pariteleri için
        # inatla üretilen spamları tamamen susturur.
        toxic_keywords = ["FDUSD", "USDC", "TUSD", "BUSD", "DAI", "PAXG", "USDTUSD", "HYPER"]
        if symbol and any(toxic in symbol.upper() for toxic in toxic_keywords):
            return # Sessizce yok say
        if message and any(toxic in message.upper() for toxic in toxic_keywords):
            return # Sessizce yok say

        self._log.appendleft({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(TRT).strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "symbol": symbol,
            "message": message,
            "level": level,
        })

    def add_throttled(
        self, 
        category: str, 
        symbol: str, 
        message: str, 
        level: str = "INFO", 
        cooldown_sec: int = 180,
        category_cooldown_sec: int = 0
    ):
        """
        Ayni kategori+sembol icin belirtilen sure dolmadan tekrar akisa yazmaz.
        category_cooldown_sec > 0 ise ayni kategorideki TUM semboller icin kuresel frenleme uygular.
        """
        now = time.time()

        # 1. Kategori bazlı küresel frenleme (örn. VCP tüm piyasada 15 dakikada en fazla 1 kez)
        if category_cooldown_sec > 0:
            cat_key = f"__GLOBAL_CAT__:{category}"
            last_cat = self._last_seen.get(cat_key, 0.0)
            if (now - last_cat) < category_cooldown_sec:
                return

        # 2. Sembol bazlı frenleme
        key = f"{category}:{symbol}"
        last = self._last_seen.get(key, 0.0)
        if (now - last) < cooldown_sec:
            return

        self._last_seen[key] = now
        if category_cooldown_sec > 0:
            self._last_seen[f"__GLOBAL_CAT__:{category}"] = now

        self.add(category, symbol, message, level)

    def get_recent(self, limit: int = 30) -> List[Dict[str, Any]]:
        return list(self._log)[:limit]


bot_thought_stream = BotThoughtStream()

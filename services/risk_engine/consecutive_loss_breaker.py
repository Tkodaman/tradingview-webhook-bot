"""
Arka Arkaya Zarar Devre Kesici (Consecutive Loss Circuit Breaker)
- Global 2 arka arkaya zarar -> 30 dk tum alimlari durdur (Hizli iyilesme)
- Sembol basina 2 zarar -> O sembolu 1 saat toxic blokla
- Gunluk maksimum zarar butcesi = 5 -> 2 saat durdur + SNIPER moda gec
- Gece 00:00'da sayaclar sifirlanir
"""
import time
import json
import os
from typing import Optional, Dict
from datetime import datetime, timezone
from core.logger import logger
from core.config import settings


BREAKER_STATE_FILE = "consecutive_loss_state.json"


class ConsecutiveLossBreaker:
    def __init__(self):
        self.consecutive_losses: int = 0
        self.daily_losses: int = 0
        self.pause_until: float = 0.0          # Unix timestamp
        self.pause_reason: str = ""
        self.symbol_losses: Dict[str, int] = {}
        self.symbol_blocks: Dict[str, float] = {}
        self.last_reset_date: str = ""
        self._load_state()

    def _load_state(self):
        try:
            if os.path.exists(BREAKER_STATE_FILE):
                with open(BREAKER_STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.consecutive_losses = data.get("consecutive_losses", 0)
                    self.daily_losses = data.get("daily_losses", 0)
                    self.pause_until = data.get("pause_until", 0.0)
                    self.pause_reason = data.get("pause_reason", "")
                    self.symbol_losses = data.get("symbol_losses", {})
                    self.symbol_blocks = data.get("symbol_blocks", {})
                    self.last_reset_date = data.get("last_reset_date", "")
        except Exception as e:
            logger.warning(f"[LOSS BREAKER] State yuklenemedi: {e}")

    def _save_state(self):
        try:
            with open(BREAKER_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "consecutive_losses": self.consecutive_losses,
                    "daily_losses": self.daily_losses,
                    "pause_until": self.pause_until,
                    "pause_reason": self.pause_reason,
                    "symbol_losses": self.symbol_losses,
                    "symbol_blocks": self.symbol_blocks,
                    "last_reset_date": self.last_reset_date
                }, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[LOSS BREAKER] State kaydedilemedi: {e}")

    def _midnight_reset_check(self):
        """Gece 00:00'da gunluk sayaclari sifirla."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self.last_reset_date != today:
            if self.consecutive_losses > 0 or self.daily_losses > 0:
                logger.info(f"[LOSS BREAKER] Gece sifirlama: Global zarar: {self.consecutive_losses}, Gunluk zarar: {self.daily_losses} temizlendi.")
            self.consecutive_losses = 0
            self.daily_losses = 0
            self.symbol_losses = {}
            self.symbol_blocks = {}
            self.last_reset_date = today
            self._save_state()

    def is_trading_paused(self, symbol: Optional[str] = None) -> tuple[bool, str]:
        """Alimlar duraklami mi? (Global veya sembol bazli)"""
        self._midnight_reset_check()
        now = time.time()

        if self.pause_until > now:
            remaining_min = int((self.pause_until - now) / 60)
            return True, f"{self.pause_reason} ({remaining_min} dakika kaldi)"
        
        if self.pause_until > 0 and self.pause_until <= now:
            logger.info("[LOSS BREAKER] Duraklama suresi doldu. Islemler yeniden aktif.")
            self.pause_until = 0.0
            self.pause_reason = ""
            self.consecutive_losses = 0
            self._save_state()

        if symbol and symbol in self.symbol_blocks:
            block_until = self.symbol_blocks[symbol]
            if block_until > now:
                rem_min = int((block_until - now) / 60)
                return True, f"SEMBOL TOXIC BLOK ({symbol}): {rem_min} dakika kaldi"
            else:
                del self.symbol_blocks[symbol]
                self._save_state()

        return False, ""

    def record_trade_result(self, symbol: str, pnl: float):
        """Her kapanan pozisyonu kaydet ve gerekirse duraklat."""
        self._midnight_reset_check()
        now = time.time()

        if pnl < 0:
            self.consecutive_losses += 1
            self.daily_losses += 1
            self.symbol_losses[symbol] = self.symbol_losses.get(symbol, 0) + 1

            logger.warning(f"[LOSS BREAKER] {symbol} zarar kapandi. Arka arkaya zarar: {self.consecutive_losses}, Gunluk toplam: {self.daily_losses}")

            if self.daily_losses >= 20:
                duration_seconds = 2 * 3600  # 2 saat
                self.pause_until = now + duration_seconds
                self.pause_reason = f"GUNLUK ZARAR BUTCESI DOLDU (20 ZARAR) — 2 SAAT DURAKLAMA"
                try:
                    settings.set_risk_mode("SNIPER")
                    logger.warning(f"[LOSS BREAKER] Gunluk maksimum zarar butcesine (20) ulasildi! SNIPER moduna gecildi ve 2 saat duraklatildi.")
                except Exception:
                    logger.warning(f"[LOSS BREAKER] Gunluk maksimum zarar butcesine (20) ulasildi! 2 saat duraklatildi.")

            elif self.consecutive_losses >= 10:
                duration_seconds = 15 * 60  # 15 dakika
                self.pause_until = now + duration_seconds
                self.pause_reason = f"10 ARKA ARKAYA ZARAR — 15 DK HIZLI DURAKLAMA"
                logger.warning(f"[LOSS BREAKER] 10 arka arkaya zarar! Tum alimlar 15 dakika duraklandi.")

            if self.symbol_losses.get(symbol, 0) >= 2:
                block_duration = 3600  # 1 saat
                self.symbol_blocks[symbol] = now + block_duration
                logger.warning(f"[LOSS BREAKER] {symbol} uzerinde 2 zarar! Sembol 1 saat boyunca toxic olarak bloklandi.")

        else:
            if self.consecutive_losses > 0:
                logger.info(f"[LOSS BREAKER] {symbol} karli kapandi. Zarar sayaci sifirlandi (onceki: {self.consecutive_losses}).")
            self.consecutive_losses = 0
            if symbol in self.symbol_losses and self.symbol_losses[symbol] > 0:
                self.symbol_losses[symbol] = 0

        self._save_state()

    def get_status(self) -> dict:
        self._midnight_reset_check()
        paused, reason = self.is_trading_paused()
        return {
            "consecutive_losses": self.consecutive_losses,
            "daily_losses": self.daily_losses,
            "symbol_losses": self.symbol_losses,
            "symbol_blocks": {s: datetime.fromtimestamp(t, tz=timezone.utc).isoformat() for s, t in self.symbol_blocks.items()},
            "is_paused": paused,
            "pause_reason": reason,
            "pause_until_iso": datetime.fromtimestamp(self.pause_until, tz=timezone.utc).isoformat() if self.pause_until > 0 else None
        }


consecutive_loss_breaker = ConsecutiveLossBreaker()

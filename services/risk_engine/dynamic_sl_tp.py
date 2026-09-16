import asyncio
from core.logger import logger
from core.config import settings


def calculate_atr_based_tp_sl(
    entry_price: float,
    atr_value: float,
    side: str = "BUY",
    is_crypto: bool = False,
) -> tuple:
    # === FIX-4: R:R orani düzetme — SL daha sıkı, TP daha geniş ===
    if entry_price <= 0 or atr_value <= 0:
        # Fallback: Minimum R:R 1:2 garantisi
        return (4.0 if is_crypto else 3.5), (1.5 if is_crypto else 1.5)

    tp_multiplier = 3.0 if is_crypto else 2.5   # FIX: 2.5/2.0 -> 3.0/2.5 (TP genisletme)
    sl_multiplier = 1.0                          # FIX: 1.5 -> 1.0 (SL sıkılaştırma)
    tp_pct = ((atr_value * tp_multiplier) / entry_price) * 100.0
    sl_pct = ((atr_value * sl_multiplier) / entry_price) * 100.0

    # === SL üst limiti %2.5 (%4.3'ten düşürüldü) ===
    sl_pct = max(1.0, min(sl_pct + 0.2, 2.5))   # FIX: max 4.3 -> 2.5
    # === TP alt limiti %2.5 (%1.8'den yükseltildi) ===
    tp_pct = max(2.5, min(tp_pct, 9.0))          # FIX: min 1.8 -> 2.5
    # === Minimum R:R 1:2 garantisi ===
    if tp_pct < sl_pct * 2.0:
        tp_pct = sl_pct * 2.0                    # FIX: 1.8x -> 2.0x (katı R:R kuralı)

    from core.logger import logger
    logger.debug(f"[ATR TP/SL] entry={entry_price} atr={atr_value:.4f} crypto={is_crypto} -> TP=%{tp_pct:.2f} SL=%{sl_pct:.2f} R:R={tp_pct/sl_pct:.2f}")
    return round(tp_pct, 2), round(sl_pct, 2)
class DynamicRiskManager:
    def __init__(self):
        # symbol -> { "high_water_mark": float, "initial_sl_set": bool }
        self.price_history = {}

        # === SIKI TRAILING STOP PARAMETRESİ ===
        # trailing_distance_pct: SL her zaman en yüksek fiyatın %1.5 altında
        # Aktivasyon yok — giriş anından itibaren geçerli, asla aşağı inmez
        self.trailing_distance_pct = 1.5   # Kullanıcı isteği: %1.5 sıkı takip

    async def on_price_update(self, symbol: str, current_price: float):
        """
        Her tick'te cagrilir. SL = max(mevcut_SL, current_price * (1 - 0.015))
        Asla asagi inmez. Aktivasyon esigi yok — giri anından itibaren aktif.
        """
        if symbol not in self.price_history:
            self.price_history[symbol] = {
                "high_water_mark": current_price,
                "initial_sl_set": False
            }

        history = self.price_history[symbol]

        # Zirveyi güncelle (asla aşağı gitme)
        if current_price > history["high_water_mark"]:
            history["high_water_mark"] = current_price

        await self._evaluate_trailing_stop(symbol, current_price, history)

    async def _evaluate_trailing_stop(self, symbol: str, current_price: float, history: dict):
        from services.market_feed.live_stream import live_trade_manager

        matched_pos = None
        for pos_id, pos in live_trade_manager.positions.items():
            if pos.symbol == symbol and pos.status == "OPEN":
                matched_pos = pos
                break

        if not matched_pos:
            return

        entry_price  = matched_pos.entry_price
        current_sl   = matched_pos.stop_loss_price
        trail_pct    = self.trailing_distance_pct / 100.0

        if matched_pos.side == "BUY":
            # === Chandelier Exit (ATR bazlı) ===
            if getattr(matched_pos, "use_chandelier_exit", False) and getattr(matched_pos, "atr_value", 0.0) > 0:
                new_sl = history["high_water_mark"] - (matched_pos.atr_value * 3.0)
                if new_sl > current_sl:
                    logger.info(f"[CHANDELIER] {symbol} SL {current_sl:.4f} -> {new_sl:.4f} (ATR bazli)")
                    matched_pos.stop_loss_price = round(new_sl, 4)
                    await self._update_broker_sl(symbol, matched_pos.take_profit_price, matched_pos.stop_loss_price)
                    await self._notify_ui(symbol, matched_pos)
                return

            # === %1.5 SIKI TRAILING STOP ===
            # SL = en yüksek görülen fiyatın %1.5 altı
            # İlk SL: giriş fiyatının %1.5 altı (eğer mevcut SL daha uzaksa ezip geçer)
            candidate_sl = history["high_water_mark"] * (1.0 - trail_pct)

            # SL'yi asla aşağı indirme; her zaman en yüksek olanı kullan
            new_sl = max(candidate_sl, current_sl)

            # Değişim varsa güncelle
            if new_sl > current_sl:
                profit_pct = ((current_price - entry_price) / entry_price) * 100.0
                logger.info(
                    f"[TRAILING SL] {symbol} | Fiyat={current_price:.4f} "
                    f"| HWM={history['high_water_mark']:.4f} "
                    f"| SL {current_sl:.4f} -> {new_sl:.4f} "
                    f"| PnL={profit_pct:+.2f}%"
                )
                matched_pos.stop_loss_price = round(new_sl, 4)
                await self._update_broker_sl(symbol, matched_pos.take_profit_price, matched_pos.stop_loss_price)
                await self._notify_ui(symbol, matched_pos)

        elif matched_pos.side == "SELL":
            # === Chandelier Exit (ATR bazlı) ===
            if getattr(matched_pos, "use_chandelier_exit", False) and getattr(matched_pos, "atr_value", 0.0) > 0:
                new_sl = history.get("low_water_mark", current_price) + (matched_pos.atr_value * 3.0)
                if new_sl < current_sl:
                    logger.info(f"[CHANDELIER] {symbol} SELL SL {current_sl:.4f} -> {new_sl:.4f} (ATR bazli)")
                    matched_pos.stop_loss_price = round(new_sl, 4)
                    await self._update_broker_sl(symbol, matched_pos.take_profit_price, matched_pos.stop_loss_price)
                    await self._notify_ui(symbol, matched_pos)
                return

            # SELL trailing: SL = en düşük fiyatın %1.5 üstü
            low_water = min(current_price, history.get("low_water_mark", current_price))
            if current_price < history.get("low_water_mark", current_price):
                history["low_water_mark"] = current_price
            candidate_sl = history.get("low_water_mark", current_price) * (1.0 + trail_pct)
            new_sl = min(candidate_sl, current_sl)   # SELL'de daha düşük olmalı
            if new_sl < current_sl:
                logger.info(f"[TRAILING SL] {symbol} SELL SL {current_sl:.4f} -> {new_sl:.4f}")
                matched_pos.stop_loss_price = round(new_sl, 4)
                await self._update_broker_sl(symbol, matched_pos.take_profit_price, matched_pos.stop_loss_price)
                await self._notify_ui(symbol, matched_pos)

    async def _update_broker_sl(self, symbol: str, tp_price: float, sl_price: float):
        if settings.trading_mode in ["LIVE", "PAPER"]:
            is_paper_mode = settings.trading_mode.upper() != "LIVE"
            from services.broker.factory import get_broker
            broker = get_broker(settings.active_broker, paper=is_paper_mode)
            if broker and hasattr(broker, 'update_bracket_orders'):
                res = broker.update_bracket_orders(symbol, take_profit_price=tp_price, stop_loss_price=sl_price)
                if res.get("status") == "success":
                    logger.info(f"✅ [BROKER SYNC] {symbol} yeni makas (TP/SL) Alpaca'ya islendi.")
                else:
                    logger.warning(f"⚠️ [BROKER SYNC ERROR] {symbol} Alpaca'ya islenemedi: {res}")

    async def _notify_ui(self, symbol: str, position):
        from routers.websocket_router import manager
        await manager.broadcast({
            "type": "DYNAMIC_SPREAD_UPDATE",
            "symbol": symbol,
            "new_sl": position.stop_loss_price,
            "new_tp": position.take_profit_price,
            "message": f"🤖 YZ Makas Guncellemesi: {symbol} yeni Stop-Loss: ${position.stop_loss_price:.4f}"
        })

dynamic_risk_manager = DynamicRiskManager()

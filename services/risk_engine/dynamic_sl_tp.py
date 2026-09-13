import asyncio
from core.logger import logger
from core.config import settings

class DynamicRiskManager:
    def __init__(self):
        # symbol -> { "last_price": 100.0, "high_water_mark": 100.0, "low_water_mark": 100.0 }
        self.price_history = {}
        # Trailing stop parametresi (örn. fiyat %1.5 artarsa, SL'yi %1 yukarı çek)
        self.trailing_activation_pct = 1.0 
        self.trailing_distance_pct = 0.5 

    async def on_price_update(self, symbol: str, current_price: float):
        """
        Called on every tick from AlpacaDataStream.
        """
        if symbol not in self.price_history:
            self.price_history[symbol] = {
                "last_price": current_price,
                "high_water_mark": current_price,
                "low_water_mark": current_price
            }
            return
            
        history = self.price_history[symbol]
        history["last_price"] = current_price
        
        if current_price > history["high_water_mark"]:
            history["high_water_mark"] = current_price
        if current_price < history["low_water_mark"]:
            history["low_water_mark"] = current_price
            
        await self._evaluate_trailing_stop(symbol, current_price, history)

    async def _evaluate_trailing_stop(self, symbol: str, current_price: float, history: dict):
        from services.market_feed.live_stream import live_trade_manager
        
        # Sadece OPEN statüsündeki pozisyonları değerlendir
        matched_pos = None
        for pos_id, pos in live_trade_manager.positions.items():
            if pos.symbol == symbol and pos.status == "OPEN":
                matched_pos = pos
                break
                
        if not matched_pos:
            return
            
        entry_price = matched_pos.entry_price
        current_sl = matched_pos.stop_loss_price
        
        if matched_pos.side == "BUY":
            # Chandelier Exit Kontrolü
            if getattr(matched_pos, "use_chandelier_exit", False) and getattr(matched_pos, "atr_value", 0.0) > 0:
                new_sl = history["high_water_mark"] - (matched_pos.atr_value * 3.0)
                if new_sl > current_sl:
                    logger.info(f"🚀 [CHANDELIER EXIT] {symbol} Zirve ({history['high_water_mark']}) görüldü (ATR: {matched_pos.atr_value:.2f}). SL {current_sl:.4f} -> {new_sl:.4f} olarak guncelleniyor.")
                    matched_pos.stop_loss_price = round(new_sl, 4)
                    await self._update_broker_sl(symbol, matched_pos.take_profit_price, matched_pos.stop_loss_price)
                    await self._notify_ui(symbol, matched_pos)
                return

            # Kâr yüzdesini hesapla
            profit_pct = ((current_price - entry_price) / entry_price) * 100.0
            
            if profit_pct >= self.trailing_activation_pct:
                # Yeni SL seviyesi
                new_sl = current_price * (1 - (self.trailing_distance_pct / 100.0))
                
                # Sadece SL'yi yukarı çekiyoruz, asla aşağı indirmeyiz
                if new_sl > current_sl:
                    logger.info(f"🚀 [DYNAMIC SL] {symbol} fiyati {current_price} oldu (Kar: %{profit_pct:.2f}). SL {current_sl:.4f} -> {new_sl:.4f} olarak guncelleniyor.")
                    matched_pos.stop_loss_price = round(new_sl, 4)
                    
                    # Broker'a ilet
                    await self._update_broker_sl(symbol, matched_pos.take_profit_price, matched_pos.stop_loss_price)
                    
                    # Arayüze WebSocket ile yansıt
                    await self._notify_ui(symbol, matched_pos)
                    
        elif matched_pos.side == "SELL":
            # Chandelier Exit Kontrolü
            if getattr(matched_pos, "use_chandelier_exit", False) and getattr(matched_pos, "atr_value", 0.0) > 0:
                new_sl = history["low_water_mark"] + (matched_pos.atr_value * 3.0)
                if new_sl < current_sl:
                    logger.info(f"🚀 [CHANDELIER EXIT] {symbol} Dip ({history['low_water_mark']}) görüldü (ATR: {matched_pos.atr_value:.2f}). SL {current_sl:.4f} -> {new_sl:.4f} olarak guncelleniyor.")
                    matched_pos.stop_loss_price = round(new_sl, 4)
                    await self._update_broker_sl(symbol, matched_pos.take_profit_price, matched_pos.stop_loss_price)
                    await self._notify_ui(symbol, matched_pos)
                return
                
            profit_pct = ((entry_price - current_price) / entry_price) * 100.0
            if profit_pct >= self.trailing_activation_pct:
                new_sl = current_price * (1 + (self.trailing_distance_pct / 100.0))
                if new_sl < current_sl: # Short için daha aşağıda (daha düşük) olması lazım
                    logger.info(f"🚀 [DYNAMIC SL] {symbol} fiyati {current_price} oldu (Kar: %{profit_pct:.2f}). SL {current_sl:.4f} -> {new_sl:.4f} olarak guncelleniyor.")
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

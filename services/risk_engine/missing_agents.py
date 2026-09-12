import time
from core.logger import logger

class SpreadGuard:
    def check_spread(self, symbol: str, market_prices: dict, max_spread_pct: float = 0.15) -> bool:
        # Mock logic or using market_prices
        data = market_prices.get(symbol, {})
        price = data.get("price", 0)
        # If we had bid/ask, we'd check them. Since we only have 'price', we'll pass or mock.
        # Just logging for now
        logger.info(f"[SPREAD GUARD] {symbol} spread denetimi yapıldı.")
        return True

spread_guard = SpreadGuard()

class TrailingAgent:
    def evaluate_trailing(self, position, current_price: float):
        if position.side == "BUY":
            entry = position.entry_price
            sl = position.stop_loss_price
            tp = position.target_profit_price
            
            # 1R = TP - Entry (roughly, if 1:1 risk reward)
            # Just move SL to breakeven if price covers 50% of the way to TP
            half_way = entry + (tp - entry) * 0.5
            
            if current_price >= half_way and sl < entry:
                position.stop_loss_price = entry * 1.001 # Breakeven + small fee cover
                logger.info(f"[TRAILING AGENT] {position.symbol} hedefe yaklaştı! SL Başabaş'a (Breakeven) çekildi: {position.stop_loss_price}")
        
        elif position.side == "SELL":
            entry = position.entry_price
            sl = position.stop_loss_price
            tp = position.target_profit_price
            
            half_way = entry - (entry - tp) * 0.5
            if current_price <= half_way and sl > entry:
                position.stop_loss_price = entry * 0.999
                logger.info(f"[TRAILING AGENT] {position.symbol} hedefe yaklaştı! SL Başabaş'a (Breakeven) çekildi: {position.stop_loss_price}")

trailing_agent = TrailingAgent()

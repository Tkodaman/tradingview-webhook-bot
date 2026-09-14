import os
from typing import Dict, Any
from core.logger import logger
from services.broker.base import BaseBroker

# Optional import, user needs to pip install alpaca-trade-api when they go live
try:
    import alpaca_trade_api as tradeapi
except ImportError:
    tradeapi = None

class AlpacaBroker(BaseBroker):
    """
    Implementation of the Alpaca Broker bridge.
    Uses environment variables ALPACA_API_KEY and ALPACA_SECRET_KEY.
    """
    
    def __init__(self, paper: bool = True):
        api_key = os.getenv("ALPACA_API_KEY", "") or os.getenv("APCA_API_KEY_ID", "")
        secret_key = os.getenv("ALPACA_SECRET_KEY", "") or os.getenv("APCA_API_SECRET_KEY", "")
        
        # alpaca_trade_api library reads these specific env var names
        if api_key:
            os.environ["APCA_API_KEY_ID"] = api_key
        if secret_key:
            os.environ["APCA_API_SECRET_KEY"] = secret_key

        self.is_paper = paper
        base_url = 'https://paper-api.alpaca.markets' if paper else 'https://api.alpaca.markets'
        
        if not tradeapi:
            logger.error("alpaca_trade_api not installed. Run 'pip install alpaca-trade-api'.")
        
        try:
            if tradeapi and api_key and secret_key:
                self.api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
                logger.info(f"[ALPACA BRIDGE] Connected {'PAPER' if paper else 'LIVE'} | Key: {api_key[:8]}...")
            else:
                self.api = None
                logger.warning("[ALPACA BRIDGE] No API key — running in simulation-only mode.")
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca API: {e}")
            self.api = None

    def get_account_balance(self) -> float:
        if not self.api:
            return 0.0
        try:
            account = self.api.get_account()
            return float(account.equity)
        except Exception as e:
            logger.error(f"Alpaca: Error fetching balance: {e}")
            return 0.0

    def get_cash_balance(self) -> float:
        if not self.api:
            return 0.0
        try:
            account = self.api.get_account()
            return float(account.cash)
        except Exception as e:
            logger.error(f"Alpaca: Error fetching cash: {e}")
            return 0.0

    def _format_symbol(self, symbol: str) -> str:
        sym = symbol.upper()
        if sym.endswith("USDT"):
            return sym.replace("USDT", "USD")
        # Keep slash removal for any other edge cases
        if "/" in sym:
            return sym.replace("/", "")
        return sym

    def place_market_order(self, symbol: str, side: str, qty: float, limit_price: float = None) -> Dict[str, Any]:
        if not self.api:
            return {"status": "error", "message": "API not initialized"}
        
        try:
            alpaca_sym = self._format_symbol(symbol)
            kwargs = {
                "symbol": alpaca_sym,
                "qty": qty,
                "side": side.lower(),
                "type": 'market' if limit_price is None else 'limit',
                "time_in_force": 'gtc'
            }
            if limit_price is not None:
                kwargs["limit_price"] = limit_price
                
            order = self.api.submit_order(**kwargs)
            logger.info(f"Alpaca {'Limit' if limit_price else 'Market'} Order Placed: {side} {qty} {alpaca_sym} - OrderID: {order.id}")
            return {"status": "success", "order_id": order.id, "details": order._raw}
        except Exception as e:
            logger.error(f"Alpaca Market Order Failed for {symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def place_bracket_order(self, symbol: str, side: str, qty: float, 
                            take_profit_price: float, stop_loss_price: float) -> Dict[str, Any]:
        if not self.api:
            return {"status": "error", "message": "API not initialized"}
            
        try:
            alpaca_sym = self._format_symbol(symbol)
            order = self.api.submit_order(
                symbol=alpaca_sym,
                qty=qty,
                side=side.lower(),
                type='market',
                time_in_force='day',
                order_class='bracket',
                take_profit=dict(
                    limit_price=take_profit_price,
                ),
                stop_loss=dict(
                    stop_price=stop_loss_price
                )
            )
            logger.info(f"Alpaca Bracket Order Placed: {side} {qty} {alpaca_sym} - OrderID: {order.id}")
            return {"status": "success", "order_id": order.id, "details": order._raw}
        except Exception as e:
            logger.error(f"Alpaca Bracket Order Failed for {symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def update_bracket_orders(self, symbol: str, take_profit_price: float = None, stop_loss_price: float = None) -> Dict[str, Any]:
        if not self.api:
            return {"status": "error"}
            
        try:
            sym = self._format_symbol(symbol)
            open_orders = self.api.list_orders(status="open", symbols=[sym])
            
            for order in open_orders:
                try:
                    if order.type == "limit" and take_profit_price:
                        # Bu Take Profit emri
                        self.api.replace_order(order.id, limit_price=take_profit_price)
                        logger.info(f"[ALPACA] {sym} TP güncellendi -> {take_profit_price}")
                    elif (order.type == "stop" or order.type == "stop_limit") and stop_loss_price:
                        # Bu Stop Loss emri
                        self.api.replace_order(order.id, stop_price=stop_loss_price)
                        logger.info(f"[ALPACA] {sym} SL güncellendi -> {stop_loss_price}")
                except Exception as ex:
                    logger.warning(f"Alpaca Emir Güncelleme Hatası ({sym}): {ex}")
                    
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Alpaca Bracket Update Failed for {symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def close_position(self, symbol: str) -> Dict[str, Any]:
        if not self.api:
            return {"status": "error"}
            
        try:
            # symbol'u Alpaca'nın anlayacağı slash'siz formata çevir
            sym = self._format_symbol(symbol)
            
            # 1) Olası açık emirleri (TP/SL braketleri) iptal et ki bakiye blokesi kalksın
            try:
                open_orders = self.api.list_orders(status="open", symbols=[sym])
                for order in open_orders:
                    self.api.cancel_order(order.id)
            except Exception as e:
                logger.warning(f"Açık emir iptali sırasında hata: {e}")
                
            # 2) Pozisyonu güvenle kapat
            res = self.api.close_position(sym)
            logger.info(f"Alpaca Position Closed: {sym}")
            return {"status": "success", "closed_position": res}
        except Exception as e:
            logger.error(f"Alpaca Close Position Failed for {symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def get_open_positions(self) -> list:
        if not self.api:
            return []
        try:
            positions = self.api.list_positions()
            return [p._raw for p in positions]
        except Exception as e:
            logger.error(f"Alpaca Fetch Positions Failed: {e}")
            return None

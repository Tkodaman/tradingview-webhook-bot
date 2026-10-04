import json
import uuid
from typing import Optional
from core.logger import logger
from core.config import settings

class AlpacaClient:
    def __init__(self):
        self.api_key = getattr(settings, "alpaca_api_key", None)
        self.api_secret = getattr(settings, "alpaca_secret_key", None)
        self.base_url = "https://paper-api.alpaca.markets/v2" if getattr(settings, "trading_mode", "PAPER") == "PAPER" else "https://api.alpaca.markets/v2"
        import requests
        self.session = requests.Session()
        if self.api_key and self.api_secret:
            self.session.headers.update({
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
                "accept": "application/json"
            })

    def submit_bracket_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        limit_price: float,
        take_profit_price: float,
        stop_loss_price: float
    ) -> Optional[dict]:
        """
        Sends an OCO (One-Cancels-Other) Bracket Order to Alpaca.
        This ensures that if the server crashes or internet drops, 
        the take-profit and stop-loss are still enforced by the broker.
        """
        
        # Alpaca Crypto Symbol Formatting & Rules
        alpaca_symbol = symbol.upper().replace("BINANCE:", "").replace("CRYPTO:", "")
        is_crypto = "USDT" in alpaca_symbol or "USD" in alpaca_symbol or len(alpaca_symbol) > 5
        
        if is_crypto:
            alpaca_symbol = alpaca_symbol.replace("USDT", "/USD")
            if "/" not in alpaca_symbol and alpaca_symbol.endswith("USD"):
                alpaca_symbol = alpaca_symbol[:-3] + "/USD"
                
        tif = "gtc" if is_crypto else "day"  # Crypto trades 24/7, 'day' is invalid
        
        # Format the Alpaca order payload
        payload = {
            "symbol": alpaca_symbol,
            "qty": str(round(qty, 5)),
            "side": side.lower(),  # 'buy' or 'sell'
            "type": "limit",       # Entry using limit to prevent slippage
            "time_in_force": tif,  
            "limit_price": str(round(limit_price, 2)),
            "order_class": "bracket",
            "take_profit": {
                "limit_price": str(round(take_profit_price, 2))
            },
            "stop_loss": {
                "stop_price": str(round(stop_loss_price, 2)),
            },
            "client_order_id": f"agy_oco_{uuid.uuid4().hex[:8]}"
        }

        # Simulation mode: Just log the payload if API keys are missing
        if not self.api_key or not self.api_secret:
            logger.info(f"🚀 [ALPACA SIMULATION] OCO Bracket Order Prepared for {symbol}:")
            logger.info(json.dumps(payload, indent=2))
            
            # Return a mock response
            return {
                "id": str(uuid.uuid4()),
                "status": "accepted",
                "simulated": True,
                "payload": payload
            }

        # TODO: Implement real REST call (requests.post) when keys are available
        try:
            import requests
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
                "Content-Type": "application/json"
            }
            response = self.session.post(f"{self.base_url}/orders", json=payload, headers=headers)
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"✅ [ALPACA OCO] Order submitted successfully: {data.get('id')}")
                return data
            else:
                logger.error(f"❌ [ALPACA OCO ERROR] {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ [ALPACA NETWORK ERROR] {e}")
            return None

    def update_bracket_orders(self, symbol: str, take_profit_price: float = None, stop_loss_price: float = None) -> dict:
        """Dynamically update TP and SL for an open position to enforce trailing stop at the broker level."""
        from services.engine.ha_manager import ha_manager
        if not ha_manager.is_leader:
            return {"status": "skipped", "message": "Node is not leader"}
            
        try:
            import requests
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
                "Content-Type": "application/json"
            }
            # Fetch open orders for this symbol
            response = self.session.get(f"{self.base_url}/orders?status=open&symbols={symbol.upper()}", headers=headers)
            if response.status_code != 200:
                return {"status": "error", "reason": "Failed to fetch open orders"}
            
            orders = response.json()
            updated = False
            for order in orders:
                order_id = order.get("id")
                order_type = order.get("type")
                
                # Update Stop Loss (type: stop or stop_limit)
                if order_type in ["stop", "stop_limit", "trailing_stop"]:
                    patch_payload = {"stop_price": str(round(stop_loss_price, 4))}
                    res = requests.patch(f"{self.base_url}/orders/{order_id}", json=patch_payload, headers=headers)
                    if res.status_code == 200: updated = True
                
                # Update Take Profit (type: limit)
                elif order_type == "limit":
                    patch_payload = {"limit_price": str(round(take_profit_price, 4))}
                    res = requests.patch(f"{self.base_url}/orders/{order_id}", json=patch_payload, headers=headers)
                    if res.status_code == 200: updated = True
            
            if updated:
                return {"status": "success"}
            return {"status": "error", "reason": "No open TP/SL orders found to update"}
        except Exception as e:
            from core.logger import logger
            logger.error(f"[ALPACA PATCH ERROR] {e}")
            return {"status": "error", "reason": str(e)}

    def sync_open_positions(self) -> list:
        if not self.api_key or not self.api_secret:
            return []
        try:
            import requests
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
                "accept": "application/json"
            }
            response = self.session.get(f"{self.base_url}/positions", headers=headers)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"[ALPACA SYNC] Successfully fetched {len(data)} open positions from broker.")
                return data
            else:
                logger.error(f"❌ [ALPACA SYNC ERROR] {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ [ALPACA SYNC NETWORK ERROR] {e}")
            return None

    def get_account_details(self) -> dict:
        if not self.api_key or not self.api_secret:
            return {}
        try:
            import requests
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
                "accept": "application/json"
            }
            response = self.session.get(f"{self.base_url}/account", headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"❌ [ALPACA ACCOUNT ERROR] {e}")
        return {}

    def get_account_balance(self) -> float:
        """Gerçek hesap bakiyesi (Equity)"""
        data = self.get_account_details()
        if data and "equity" in data:
            return float(data["equity"])
        
        # Fallback
        from core.config import settings
        return float(getattr(settings, "base_portfolio_size", 5000.0))

    def get_available_cash(self) -> float:
        """Kullanılabilir serbest nakit / alım gücü (Buying Power)"""
        data = self.get_account_details()
        if data and "buying_power" in data:
            return float(data["buying_power"])
            
        # Fallback
        from core.config import settings
        return float(getattr(settings, "base_portfolio_size", 5000.0))


    def get_bid_ask_spread(self, symbol: str) -> Optional[float]:
        """
        Fetches the latest quote (Bid and Ask) from Alpaca Data API and calculates the spread percentage.
        Returns the spread as a percentage (e.g., 0.15 for 0.15%).
        """
        if not self.api_key or not self.api_secret:
            return None

        try:
            import requests
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
                "accept": "application/json"
            }
            # Alpaca Data API uses a different base URL than trading API
            data_url = "https://data.alpaca.markets/v2/stocks"
            
            # Simple heuristic for Crypto vs Stock (e.g. BTC/USD or BTCUSDT)
            is_crypto = "USD" in symbol.upper() or len(symbol) > 5
            
            if is_crypto:
                # Format standard crypto symbol like BTC/USD for Alpaca
                clean_sym = symbol.upper().replace("BINANCE:", "").replace("CRYPTO:", "").replace("USDT", "/USD")
                if "/" not in clean_sym and clean_sym.endswith("USD"):
                    clean_sym = clean_sym[:-3] + "/USD"
                
                req_url = f"https://data.alpaca.markets/v1beta3/crypto/us/latest/quotes?symbols={clean_sym}"
                response = self.session.get(req_url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    quotes = data.get("quotes", {})
                    quote = quotes.get(clean_sym)
                    if quote:
                        bp = quote.get("bp", 0)  # bid price
                        ap = quote.get("ap", 0)  # ask price
                        if bp > 0 and ap > 0:
                            spread_pct = ((ap - bp) / bp) * 100.0
                            return round(spread_pct, 4)
            else:
                # Stock quote
                req_url = f"{data_url}/{symbol.upper()}/quotes/latest"
                response = self.session.get(req_url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    quote = data.get("quote", {})
                    bp = quote.get("bp", 0)
                    ap = quote.get("ap", 0)
                    if bp > 0 and ap > 0:
                        spread_pct = ((ap - bp) / bp) * 100.0
                        return round(spread_pct, 4)
            
            # Fallback if no quote or error
            return None
        except Exception as e:
            logger.error(f"❌ [ALPACA SPREAD FETCH ERROR] {e}")
            return None

    def get_current_price(self, symbol: str) -> float:
        """Fetches the latest trade price from Alpaca Data API"""
        if not self.api_key or not self.api_secret:
            return 0.0
            
        try:
            import requests
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
                "accept": "application/json"
            }
            data_url = "https://data.alpaca.markets/v2/stocks"
            is_crypto = "USD" in symbol.upper() or len(symbol) > 5
            
            if is_crypto:
                clean_sym = symbol.upper().replace("BINANCE:", "").replace("CRYPTO:", "").replace("USDT", "/USD")
                if "/" not in clean_sym and clean_sym.endswith("USD"):
                    clean_sym = clean_sym[:-3] + "/USD"
                
                req_url = f"https://data.alpaca.markets/v1beta3/crypto/us/latest/trades?symbols={clean_sym}"
                response = self.session.get(req_url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    trades = data.get("trades", {})
                    trade = trades.get(clean_sym)
                    if trade:
                        return float(trade.get("p", 0.0))
            else:
                req_url = f"{data_url}/{symbol.upper()}/trades/latest"
                response = self.session.get(req_url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    trade = data.get("trade", {})
                    return float(trade.get("p", 0.0))
            return 0.0
        except Exception as e:
            logger.error(f"❌ [ALPACA PRICE FETCH ERROR] {e}")
            return 0.0

alpaca_client = AlpacaClient()

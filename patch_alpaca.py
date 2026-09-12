import uuid

new_logic = '''import json
import uuid
from typing import Optional
from core.logger import logger
from core.config import settings

class AlpacaClient:
    def __init__(self):
        self.api_key = getattr(settings, "alpaca_api_key", None)
        self.api_secret = getattr(settings, "alpaca_secret_key", None)
        self.base_url = "https://paper-api.alpaca.markets/v2" if getattr(settings, "trading_mode", "PAPER") == "PAPER" else "https://api.alpaca.markets/v2"

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
        
        # Format the Alpaca order payload
        payload = {
            "symbol": symbol.upper(),
            "qty": str(round(qty, 5)),
            "side": side.lower(),  # 'buy' or 'sell'
            "type": "limit",       # Entry using limit to prevent slippage
            "time_in_force": "gtc",
            "limit_price": str(round(limit_price, 2)),
            "order_class": "bracket",
            "take_profit": {
                "limit_price": str(round(take_profit_price, 2))
            },
            "stop_loss": {
                "stop_price": str(round(stop_loss_price, 2)),
                # Optional: "limit_price" for stop-limit order, 
                # but "stop_price" triggers a market order to ensure exit during a crash
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
            response = requests.post(f"{self.base_url}/orders", json=payload, headers=headers)
            
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
            response = requests.get(f"{self.base_url}/positions", headers=headers)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"🔄 [ALPACA SYNC] Successfully fetched {len(data)} open positions from broker.")
                return data
            else:
                logger.error(f"❌ [ALPACA SYNC ERROR] {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"❌ [ALPACA SYNC NETWORK ERROR] {e}")
            return []

    def get_bid_ask_spread(self, symbol: str) -> float:
        """
        Fetches the latest quote (Bid and Ask) from Alpaca Data API and calculates the spread percentage.
        Returns the spread as a percentage (e.g., 0.15 for 0.15%).
        """
        if not self.api_key or not self.api_secret:
            return 0.0  # Simulated mode

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
                clean_sym = symbol.upper().replace("USDT", "/USD")
                if "/" not in clean_sym and clean_sym.endswith("USD"):
                    clean_sym = clean_sym[:-3] + "/USD"
                
                req_url = f"https://data.alpaca.markets/v1beta3/crypto/us/latest/quotes?symbols={clean_sym}"
                response = requests.get(req_url, headers=headers, timeout=2.0)
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
                response = requests.get(req_url, headers=headers, timeout=2.0)
                if response.status_code == 200:
                    data = response.json()
                    quote = data.get("quote", {})
                    bp = quote.get("bp", 0)
                    ap = quote.get("ap", 0)
                    if bp > 0 and ap > 0:
                        spread_pct = ((ap - bp) / bp) * 100.0
                        return round(spread_pct, 4)
            
            # Fallback if no quote or error
            return 0.0
        except Exception as e:
            logger.error(f"❌ [ALPACA SPREAD FETCH ERROR] {e}")
            return 0.0

alpaca_client = AlpacaClient()
'''

with open('services/broker/alpaca_client.py', 'w', encoding='utf-8') as f:
    f.write(new_logic)

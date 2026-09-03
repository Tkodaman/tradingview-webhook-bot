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

alpaca_client = AlpacaClient()

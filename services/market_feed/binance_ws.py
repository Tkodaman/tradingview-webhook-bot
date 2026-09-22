import json
import asyncio
import websockets
from core.logger import logger

class BinanceWebsocketStream:
    """
    SOTA Data Feed Engine (Phase 1 Upgrade)
    Connects to Binance Public WebSocket for sub-second tick data without API limits or SSL errors.
    """
    def __init__(self):
        self.stream_url = "wss://stream.binance.com:9443/ws"
        self.active_streams = []
        self.latest_prices = {}

    def get_price(self, symbol: str) -> float:
        return self.latest_prices.get(symbol.upper(), 0.0)

    async def _handle_message(self, message):
        data = json.loads(message)
        # Handle miniTicker stream
        if 'e' in data and data['e'] == '24hrMiniTicker':
            symbol = data['s']
            price = float(data['c'])
            self.latest_prices[symbol] = price
            # logger.debug(f"[WS] {symbol}: {price}")

    async def start_stream(self, symbols: list):
        """
        Starts the websocket connection for the given symbols.
        Example symbols: ["SUIUSDT", "NEARUSDT", "BTCUSDT"]
        """
        self.active_streams = [f"{sym.lower()}@miniTicker" for sym in symbols]
        
        subscribe_payload = {
            "method": "SUBSCRIBE",
            "params": self.active_streams,
            "id": 1
        }
        
        while True:
            try:
                logger.info(f"[WS DATA FEED] Connecting to Binance WS for {symbols}...")
                async with websockets.connect(self.stream_url) as ws:
                    await ws.send(json.dumps(subscribe_payload))
                    logger.info("[WS DATA FEED] Connected and Subscribed successfully.")
                    
                    while True:
                        msg = await ws.recv()
                        await self._handle_message(msg)
                        
            except Exception as e:
                logger.error(f"[WS DATA FEED] Connection lost: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    # Test execution
    async def test():
        ws = BinanceWebsocketStream()
        asyncio.create_task(ws.start_stream(["SUIUSDT", "NEARUSDT"]))
        for i in range(5):
            await asyncio.sleep(2)
            print(f"Latest SUI: {ws.get_price('SUIUSDT')}")
            print(f"Latest NEAR: {ws.get_price('NEARUSDT')}")
            
    asyncio.run(test())

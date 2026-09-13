import asyncio
import json
import traceback
try:
    import websockets
except ImportError:
    import os
    os.system('pip install websockets')
    import websockets

from core.logger import logger
from core.config import settings
from routers.websocket_router import manager

class AlpacaDataStream:
    def __init__(self):
        # IEX for stocks
        self.ws_url_stocks = "wss://stream.data.alpaca.markets/v2/iex"
        # Crypto
        self.ws_url_crypto = "wss://stream.data.alpaca.markets/v1beta3/crypto/us"
        
        self.api_key = settings.alpaca_api_key.strip() if settings.alpaca_api_key else ""
        self.api_secret = settings.alpaca_secret_key.strip() if settings.alpaca_secret_key else ""
        
        self.active_stock_symbols = set()
        self.active_crypto_symbols = set()
        
        self.stock_ws = None
        self.crypto_ws = None

    async def connect_and_listen(self):
        asyncio.create_task(self._listen_stocks())
        asyncio.create_task(self._listen_crypto())
        asyncio.create_task(self._monitor_active_positions())

    async def _authenticate(self, websocket):
        # İlk bağlantı onayını oku
        response = await websocket.recv()
        data = json.loads(response)
        if not (isinstance(data, list) and len(data) > 0 and data[0].get("T") == "success" and data[0].get("msg") == "connected"):
            logger.error(f"[ALPACA AUTH] Ilk baglanti basarisiz. Yanit: {data}")
            return False

        auth_payload = {
            "action": "auth",
            "key": self.api_key,
            "secret": self.api_secret
        }
        await websocket.send(json.dumps(auth_payload))
        response = await websocket.recv()
        data = json.loads(response)
        
        if isinstance(data, list) and len(data) > 0 and data[0].get("T") == "success" and data[0].get("msg") == "authenticated":
            return True
        logger.error(f"[ALPACA AUTH] Auth failed. Server response: {data}")
        return False

    async def _listen_stocks(self):
        while True:
            try:
                async with websockets.connect(self.ws_url_stocks) as websocket:
                    self.stock_ws = websocket
                    if not await self._authenticate(websocket):
                        logger.error("[ALPACA DATA WS - STOCKS] Yetkilendirme basarisiz.")
                        await asyncio.sleep(10)
                        continue
                        
                    logger.info("[ALPACA DATA WS - STOCKS] Baglanti basarili.")
                    
                    if self.active_stock_symbols:
                        await self._subscribe_stocks(list(self.active_stock_symbols))
                        
                    while True:
                        msg = await websocket.recv()
                        await self._process_message(msg, is_crypto=False)
            except Exception as e:
                logger.warning(f"[ALPACA DATA WS - STOCKS] Hata/Kopma: {e}")
                self.stock_ws = None
                await asyncio.sleep(5)

    async def _listen_crypto(self):
        while True:
            try:
                async with websockets.connect(self.ws_url_crypto) as websocket:
                    self.crypto_ws = websocket
                    if not await self._authenticate(websocket):
                        logger.error("[ALPACA DATA WS - CRYPTO] Yetkilendirme basarisiz.")
                        await asyncio.sleep(10)
                        continue
                        
                    logger.info("[ALPACA DATA WS - CRYPTO] Baglanti basarili.")
                    
                    if self.active_crypto_symbols:
                        await self._subscribe_crypto(list(self.active_crypto_symbols))
                        
                    while True:
                        msg = await websocket.recv()
                        await self._process_message(msg, is_crypto=True)
            except Exception as e:
                logger.warning(f"[ALPACA DATA WS - CRYPTO] Hata/Kopma: {e}")
                self.crypto_ws = None
                await asyncio.sleep(5)

    async def _subscribe_stocks(self, symbols):
        if not self.stock_ws or not symbols: return
        payload = {
            "action": "subscribe",
            "trades": symbols,
            "quotes": symbols
        }
        await self.stock_ws.send(json.dumps(payload))
        logger.info(f"[ALPACA DATA WS - STOCKS] Abonelik guncellendi: {symbols}")

    async def _subscribe_crypto(self, symbols):
        if not self.crypto_ws or not symbols: return
        # Format crypto symbols for data API (e.g. BTC/USD)
        formatted_symbols = []
        for s in symbols:
            s_up = s.upper()
            if s_up.endswith("USDT"): s_up = s_up.replace("USDT", "USD")
            if "/" not in s_up and s_up.endswith("USD"): s_up = s_up[:-3] + "/USD"
            formatted_symbols.append(s_up)
            
        payload = {
            "action": "subscribe",
            "trades": formatted_symbols,
            "quotes": formatted_symbols
        }
        await self.crypto_ws.send(json.dumps(payload))
        logger.info(f"[ALPACA DATA WS - CRYPTO] Abonelik guncellendi: {formatted_symbols}")

    async def _process_message(self, msg, is_crypto):
        try:
            data = json.loads(msg)
            for item in data:
                msg_type = item.get("T")
                if msg_type in ["q", "t"]: # Quote or Trade
                    sym = item.get("S", "")
                    
                    # Normalize crypto symbol back
                    if is_crypto:
                        sym = sym.replace("/", "").replace("USD", "USDT")
                        
                    price = item.get("p") or item.get("bp") or item.get("ap") # trade price, or bid/ask
                    
                    if price:
                        from services.risk_engine.dynamic_sl_tp import dynamic_risk_manager
                        await dynamic_risk_manager.on_price_update(sym, float(price))
                        
        except Exception as e:
            logger.error(f"[ALPACA DATA WS] Mesaj isleme hatasi: {e}")

    async def _monitor_active_positions(self):
        """Monitors LiveTradeManager for open positions and updates subscriptions dynamically."""
        from services.market_feed.live_stream import live_trade_manager
        while True:
            try:
                current_stocks = set()
                current_crypto = set()
                
                for pos_id, pos in live_trade_manager.positions.items():
                    if pos.status == "OPEN":
                        if pos.symbol.endswith("USDT") or pos.symbol in ["BTC", "ETH", "SOL", "BNB"]:
                            current_crypto.add(pos.symbol)
                        else:
                            current_stocks.add(pos.symbol)
                            
                if current_stocks != self.active_stock_symbols:
                    self.active_stock_symbols = current_stocks
                    await self._subscribe_stocks(list(self.active_stock_symbols))
                    
                if current_crypto != self.active_crypto_symbols:
                    self.active_crypto_symbols = current_crypto
                    await self._subscribe_crypto(list(self.active_crypto_symbols))
                    
            except Exception as e:
                logger.error(f"[ALPACA DATA WS] Monitor error: {e}")
                
            await asyncio.sleep(5) # Check every 5 seconds

alpaca_data_stream = AlpacaDataStream()

async def start_alpaca_data_stream():
    await alpaca_data_stream.connect_and_listen()

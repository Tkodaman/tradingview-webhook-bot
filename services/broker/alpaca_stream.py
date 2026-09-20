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
from services.market_feed.live_stream import live_trade_manager

class AlpacaTradeStream:
    def __init__(self):
        if settings.trading_mode == "PAPER":
            self.ws_url = "wss://paper-api.alpaca.markets/stream"
        else:
            self.ws_url = "wss://api.alpaca.markets/stream"
            
        self.api_key = settings.alpaca_api_key
        self.api_secret = settings.alpaca_secret_key
        self.is_connected = False
        self.fallback_task = None
        
    async def connect_and_listen(self):
        retry_count = 0
        
        # Start fallback background task
        if not self.fallback_task:
            self.fallback_task = asyncio.create_task(self.fallback_polling_loop())
            
        while True:
            try:
                backoff_time = min(2 ** retry_count, 60)
                if retry_count > 0:
                    logger.warning(f"[ALPACA WS] Bağlantı koptu. Fallback Polling devrede. Yeniden bağlanılıyor (Backoff: {backoff_time}s)")
                    await asyncio.sleep(backoff_time)
                
                logger.info(f"[ALPACA WS] Baglaniliyor: {self.ws_url}")
                async with websockets.connect(self.ws_url) as websocket:
                    self.is_connected = True
                    retry_count = 0
                    
                    auth_payload = {
                        "action": "auth",
                        "key": self.api_key,
                        "secret": self.api_secret
                    }
                    await websocket.send(json.dumps(auth_payload))
                    
                    auth_response = await websocket.recv()
                    auth_data = json.loads(auth_response)
                    
                    is_authorized = False
                    if isinstance(auth_data, list) and len(auth_data) > 0:
                        is_authorized = auth_data[0].get("data", {}).get("status") == "authorized"
                    elif isinstance(auth_data, dict):
                        is_authorized = auth_data.get("data", {}).get("status") == "authorized"
                        
                    if is_authorized:
                        logger.info("[ALPACA WS] Yetkilendirme başarılı.")
                    else:
                        logger.error(f"[ALPACA WS] Yetkilendirme hatası: {auth_data}")
                        self.is_connected = False
                        await asyncio.sleep(10)
                        continue
                        
                    sub_payload = {
                        "action": "listen",
                        "data": {
                            "streams": ["trade_updates"]
                        }
                    }
                    await websocket.send(json.dumps(sub_payload))
                    logger.info("[ALPACA WS] trade_updates kanalına bağlanıldı. (Sıfır-Gecikme devrede)")
                    
                    while True:
                        msg = await websocket.recv()
                        await self._process_message(msg)
                        
            except websockets.ConnectionClosed:
                self.is_connected = False
                logger.warning("[ALPACA WS] Bağlantı koptu (ConnectionClosed).")
                retry_count += 1
            except Exception as e:
                self.is_connected = False
                logger.error(f"[ALPACA WS] Beklenmeyen hata: {e}")
                logger.debug(traceback.format_exc())
                retry_count += 1

    async def _process_message(self, msg: str):
        try:
            data = json.loads(msg)
            if isinstance(data, list):
                for item in data:
                    await self._handle_event(item)
            elif isinstance(data, dict):
                await self._handle_event(data)
        except Exception as e:
            logger.error(f"[ALPACA WS] Mesaj isleme hatasi: {e}")

    async def _handle_event(self, item: dict):
        if item.get("stream") != "trade_updates":
            return
            
        data = item.get("data", {})
        event_type = data.get("event")
        order = data.get("order", {})
        symbol = order.get("symbol")
        
        if event_type == "fill":
            side = order.get("side")
            qty = order.get("filled_qty")
            price = data.get("price") or order.get("filled_avg_price")
            
            logger.info(f"⚡ [ALPACA WS ZERO-LATENCY] {symbol} FILL ({side}) @ {price} | Qty: {qty}")
            
            matched_pos = None
            for pos_id, pos in live_trade_manager.positions.items():
                if pos.symbol == symbol and pos.status == "OPEN":
                    matched_pos = pos
                    break
                    
            if matched_pos:
                if (matched_pos.side == "BUY" and side == "sell") or (matched_pos.side == "SELL" and side == "buy"):
                    reason = "CLOSED_BY_BROKER_TP_SL_OR_MANUAL"
                    live_trade_manager.close_position(matched_pos.id, reason)
                    
                    await manager.broadcast({
                        "type": "TRADE_UPDATE",
                        "symbol": symbol,
                        "action": "CLOSED",
                        "price": price,
                        "message": f"{symbol} emri broker tarafında kapandı (SL/TP tetiklendi)."
                    })
                    
        elif event_type == "canceled":
            logger.info(f"🚫 [ALPACA WS EVENT] {symbol} EMİR İPTAL (Canceled).")

    async def fallback_polling_loop(self):
        """
        Runs continuously in the background. Polls the REST API periodically 
        to ensure no positions are left hanging (e.g. closed by SL/TP offline) 
        and adds any manual positions opened directly on Alpaca.
        """
        while True:
            try:
                from services.broker.factory import get_broker
                broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
                if broker and broker.api:
                    raw_positions = broker.get_open_positions()
                    if raw_positions is None:
                        logger.warning("[FALLBACK POLLING] Fetch positions failed (Network error?). Skipping cycle.")
                        await asyncio.sleep(5)
                        continue
                        
                    active_symbols = [p.get("symbol") for p in raw_positions if p.get("symbol")]
                    
                    # 1. Local'de açık olup Alpaca'da olmayanları kapat
                    closed_locally = []
                    import datetime
                    for pos_id, pos in live_trade_manager.positions.items():
                        if pos.status == "OPEN":
                            formatted_sym = broker._format_symbol(pos.symbol) if hasattr(broker, "_format_symbol") else pos.symbol
                            if formatted_sym not in active_symbols:
                                # GRACE PERIOD (2 dk): Yeni açılan emirler Alpaca'da henüz PENDING (bekleyen/kuyrukta) olabilir.
                                try:
                                    opened_dt = datetime.datetime.fromisoformat(pos.opened_at)
                                    # Ensure both are timezone aware or naive to compare safely
                                    now_utc = datetime.datetime.now(datetime.timezone.utc)
                                    if opened_dt.tzinfo is None:
                                        opened_dt = opened_dt.replace(tzinfo=datetime.timezone.utc)
                                        
                                    diff_seconds = (now_utc - opened_dt).total_seconds()
                                    if diff_seconds < 120:
                                        # Emir henüz 2 dakikadan yeni, PENDING olabilir, hemen kapatma!
                                        continue
                                        
                                    # Fallback: Maybe order is still 'new'/'accepted' but >120s? Check open orders.
                                    try:
                                        open_orders = broker.api.list_orders(status='open')
                                        open_order_symbols = [broker._format_symbol(o.symbol) for o in open_orders] if open_orders else []
                                        if formatted_sym in open_order_symbols:
                                            logger.info(f"⏳ [PENDING ORDER] {pos.symbol} emri {diff_seconds} saniyedir Alpaca'da acik (beklemede). Kapatilmiyor.")
                                            continue
                                    except Exception as ex:
                                        logger.debug(f"Open orders fetch error: {ex}")
                                        pass
                                except Exception as e:
                                    logger.debug(f"Grace period time parsing error: {e}")
                                    pass
                                    
                                closed_locally.append(pos)
                            
                    for pos in closed_locally:
                        logger.info(f"⚠️ [FALLBACK POLLING] {pos.symbol} pozisyonu REST API'de bulunamadi. Kapanis yansitiliyor.")
                        live_trade_manager.close_position(pos.id, "CLOSED_OFFLINE_SYNC")
                        await manager.broadcast({
                            "type": "TRADE_UPDATE",
                            "symbol": pos.symbol,
                            "action": "CLOSED",
                            "price": 0,
                            "message": f"{pos.symbol} emri baglanti kopukken veya manuel (Fallback) kapandi."
                        })

                    # 2. Alpaca'da açık olup Local'de olmayanları ekle
                    live_trade_manager.sync_with_broker()
                    
            except Exception as e:
                logger.error(f"[FALLBACK POLLING ERROR] {e}")
        
            # Poll every 15 seconds continuously for Azami Dikkat sync
            await asyncio.sleep(15)

alpaca_trade_stream = AlpacaTradeStream()

async def start_alpaca_stream():
    await alpaca_trade_stream.connect_and_listen()

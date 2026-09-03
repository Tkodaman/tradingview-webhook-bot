import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from services.market_feed.live_stream import LiveTradeManager

router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
                
        for connection in dead_connections:
            self.active_connections.remove(connection)

manager = ConnectionManager()

# Background task to send live updates
async def live_data_broadcaster(live_trade_manager: LiveTradeManager):
    while True:
        try:
            if manager.active_connections:
                prices = live_trade_manager.get_live_prices()
                summary = {
                    "account_balance": live_trade_manager.account_balance,
                    "available_cash": live_trade_manager.available_cash,
                    "total_commissions_paid": live_trade_manager.total_commissions_paid,
                    "active_positions": [p.dict() for p in live_trade_manager.positions.values() if p.status == "OPEN"]
                }
                
                payload = {
                    "type": "LIVE_MARKET",
                    "data": {
                        "live_prices": prices,
                        "summary": summary
                    }
                }
                await manager.broadcast(payload)
        except Exception as e:
            from core.logger import logger
            logger.error(f"Broadcaster error: {e}")
        
        await asyncio.sleep(1.5)  # 1.5 saniyelik yayın periyodu

@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "PING":
                await websocket.send_text("PONG")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

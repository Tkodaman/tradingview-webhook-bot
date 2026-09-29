import asyncio
import json
import time
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from services.market_feed.live_stream import LiveTradeManager

# Bot baslangic zamani (uptime hesabi icin)
_BOT_START_TIME = time.time()

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
    last_multiplier = None
    while True:
        try:
            if manager.active_connections:
                # UI shouldn't fetch, just use the data fetched by auto_runner.py to keep it extremely fast
                prices = await asyncio.to_thread(live_trade_manager.get_live_prices, fetch_new=False)
                
                # Check Supervisor Agent Risk Profile
                try:
                    from services.engine.supervisor_agent import supervisor_agent
                    current_mult = supervisor_agent.calculate_dynamic_budget_multiplier(prices)
                    if current_mult != last_multiplier:
                        last_multiplier = current_mult
                        await manager.broadcast({
                            "type": "RISK_UPDATE",
                            "multiplier": current_mult
                        })
                except Exception:
                    pass
                # Varsayılan (Simülasyon Modu veya Alpaca kapalıysa)
                effective_balance = live_trade_manager.account_balance
                real_available_cash = live_trade_manager.available_cash
                
                # Dashboard'a gönderilecek pozisyon listesi
                # live_trade_manager arka planda zaten Alpaca ile senkronize edildiği için (Ghost Cleanup dahil),
                # burada tekrar tekrar her milisaniyede internet üzerinden Alpaca'ya HTTP isteği atmak 
                # (blocking request) tüm sunucuyu kitler ve gecikme yaratır. Doğrudan yerel belleği kullanıyoruz.
                positions_for_dashboard = [
                    p.model_dump() for p in live_trade_manager.positions.values() if p.status in ["OPEN", "SHADOW_OPEN"]
                ]


                # Bot uptime hesapla
                elapsed = int(time.time() - _BOT_START_TIME)
                h = elapsed // 3600
                m = (elapsed % 3600) // 60
                s = elapsed % 60
                bot_uptime_str = f"{h:02d}:{m:02d}:{s:02d}"
                last_scan_str = datetime.now(timezone.utc).strftime("%H:%M:%S")

                total_open_comm = sum(p.commission_fees for p in live_trade_manager.positions.values() if p.status == "OPEN")
                summary = {
                    "account_balance": round(effective_balance, 2),
                    "available_cash": round(real_available_cash, 2),
                    "total_commissions_paid": round(live_trade_manager.total_commissions_paid + total_open_comm, 2),
                    "active_positions": positions_for_dashboard,
                    "bot_uptime": bot_uptime_str,
                    "last_scan": last_scan_str
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
        
        await asyncio.sleep(0.4)  # 0.4 saniyelik ultra hızlı yayın periyodu

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

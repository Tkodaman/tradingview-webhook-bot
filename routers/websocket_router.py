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
                prices = live_trade_manager.get_live_prices()
                
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
                
                # === ALPACA KAYNAK HAKIKATI (Single Source of Truth) ===
                # LIVE/PAPER modda tum pozisyon ve PnL verileri TAMAMEN Alpaca'dan gelir.
                # Botun yerel hesaplari UI'ya HICBIR ZAMAN yansimaz.
                alpaca_positions_for_ui = []
                try:
                    from core.config import settings
                    if settings.trading_mode in ["LIVE", "PAPER"]:
                        from services.broker.factory import get_broker
                        from core.logger import logger
                        broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
                        if broker and broker.api:
                            alpaca_eq = float(broker.get_account_balance())
                            raw_positions = broker.get_open_positions() or []
                            active_assets = sum(float(p.get("market_value", 0)) for p in raw_positions)

                            # 1. Alpaca sembol -> bot pozisyon eslestirmesi (yerel PnL'i Alpaca ile ezdik)
                            synced_symbols = set()
                            for rp in raw_positions:
                                alpaca_sym = rp.get("symbol", "")           # ornekle "ETHUSD"
                                alpaca_sym_t = alpaca_sym + "T"             # ornekle "ETHUSDT"
                                avg_entry = float(rp.get("avg_entry_price", 0) or 0)
                                curr_price = float(rp.get("current_price", 0) or 0)
                                unreal_pl  = float(rp.get("unrealized_pl", 0) or 0)
                                unreal_plpc= float(rp.get("unrealized_plpc", 0) or 0) * 100
                                qty        = float(rp.get("qty", 0) or 0)
                                mkt_val    = float(rp.get("market_value", 0) or 0)

                                # Bot'taki eslesen pozisyonu bul ve ALPACA verileriyle ezip gec
                                for p in live_trade_manager.positions.values():
                                    if p.symbol in (alpaca_sym, alpaca_sym_t):
                                        if p.status == "PENDING_BROKER":
                                            p.status = "OPEN"
                                        if avg_entry > 0:
                                            p.entry_price = avg_entry
                                        if curr_price > 0:
                                            p.current_price = curr_price
                                        p.unrealized_pnl     = round(unreal_pl, 2)
                                        p.unrealized_pnl_pct = round(unreal_plpc, 4)
                                        p.quantity           = qty
                                        p.nominal_value      = mkt_val
                                        synced_symbols.add(p.symbol)

                                # UI icin Alpaca'dan gelen ham veriyi hazirla (kesin deger)
                                alpaca_positions_for_ui.append({
                                    "id": f"ALPACA-{alpaca_sym}",
                                    "symbol": alpaca_sym_t,            # Bot formatinda goster
                                    "market": "CRYPTO" if alpaca_sym.endswith("USD") and len(alpaca_sym) <= 8 else "NASDAQ",
                                    "side": rp.get("side", "long").upper(),
                                    "entry_price": avg_entry,
                                    "current_price": curr_price,
                                    "quantity": qty,
                                    "nominal_value": mkt_val,
                                    "unrealized_pnl": round(unreal_pl, 2),
                                    "unrealized_pnl_pct": round(unreal_plpc, 4),
                                    "target_profit_price": 0,
                                    "stop_loss_price": 0,
                                    "break_even_trigger_price": 0,
                                    "status": "OPEN",
                                    "opened_at": "",
                                    "source": "ALPACA_LIVE",  # UI'da gosterim icin
                                })

                            effective_balance = min(alpaca_eq, 5000.0)
                            real_available_cash = max(0.0, effective_balance - active_assets)
                            logger.debug(f"[WS SYNC] {len(raw_positions)} Alpaca pozisyonu UI'a aktarildi.")
                except Exception as sync_err:
                    from core.logger import logger
                    logger.warning(f"[WS SYNC ERROR] Alpaca senkronizasyon hatasi: {sync_err}")

                # Dashboard'a gonderilecek pozisyon listesi:
                # LIVE/PAPER modda: Alpaca'dan gelen gercek veriler
                # SIMULATION modda: Bot'un yerel listesi
                if alpaca_positions_for_ui:
                    positions_for_dashboard = alpaca_positions_for_ui
                else:
                    positions_for_dashboard = [
                        p.model_dump() for p in live_trade_manager.positions.values() if p.status == "OPEN"
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

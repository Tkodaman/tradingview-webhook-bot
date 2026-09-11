from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from services.market_feed.live_stream import live_trade_manager, ActivePosition
from core.config import settings

router = APIRouter()

class OpenPositionRequest(BaseModel):
    symbol: str = Field("NVDA", description="Sembol")
    capital: float = Field(100.0, description="Kullanılacak Sermaye ($ / ₺)")
    side: str = Field("BUY", description="BUY veya SELL")
    tp_pct: float = Field(3.0, description="Kâr Al Yüzdesi")
    sl_pct: float = Field(1.5, description="Zarar Kes Yüzdesi")

@router.get("/active")
async def get_active_positions():
    """
    Canlı Açık Pozisyonlar ve Kâr/Zarar Listesi
    """
    if settings.trading_mode in ["LIVE", "PAPER"]:
        from services.broker.factory import get_broker
        broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
        if broker and broker.api:
            try:
                # Canlı bakiye ve pozisyonları çek
                real_balance = broker.get_account_balance()
                # Kullanıcı isteği üzerine 1000$ sanal sınır
                effective_balance = min(1000.0, real_balance)
                
                raw_positions = broker.get_open_positions()
                active_list = []
                for p in raw_positions:
                    sym = p.get("symbol")
                    local_pos = next((lp for lp in live_trade_manager.positions.values() if lp.symbol == sym and lp.status == "OPEN"), None)
                    opened_at_val = local_pos.opened_at if local_pos else "Senkronize"

                    entry_price = float(p.get("avg_entry_price", 0))
                    side = "BUY" if p.get("side") == "long" else "SELL"
                    
                    tp_price = 0.0
                    sl_price = 0.0
                    
                    if entry_price > 0:
                        from services.engine.experience_memory_engine import experience_memory_engine
                        dyn_tp_pct, dyn_sl_pct = experience_memory_engine.get_dynamic_margins(sym)
                        if side == "BUY":
                            tp_price = entry_price * (1.0 + (dyn_tp_pct / 100.0))
                            sl_price = entry_price * (1.0 - (dyn_sl_pct / 100.0))
                        else:
                            tp_price = entry_price * (1.0 - (dyn_tp_pct / 100.0))
                            sl_price = entry_price * (1.0 + (dyn_sl_pct / 100.0))
                            
                    active_list.append({
                        "id": str(p.get("id", f"POS-{sym}")),
                        "symbol": sym,
                        "market": str(p.get("asset_class", "STOCK")).upper(),
                        "side": side,
                        "entry_price": entry_price,
                        "current_price": float(p.get("current_price", 0)),
                        "quantity": float(p.get("qty", 0)),
                        "nominal_value": float(p.get("market_value", 0)),
                        "target_profit_price": round(tp_price, 4),
                        "stop_loss_price": round(sl_price, 4),
                        "unrealized_pnl": float(p.get("unrealized_pl", 0)),
                        "unrealized_pnl_pct": float(p.get("unrealized_plpc", 0)) * 100,
                        "opened_at": opened_at_val,
                        "status": "OPEN"
                    })
                
                return {
                    "account_balance": round(effective_balance, 2),
                    "available_cash": round(effective_balance, 2), # Basitleştirildi
                    "total_commissions_paid": 0.0,
                    "active_positions": active_list,
                    "history": live_trade_manager.trade_history[:10]
                }
            except Exception as e:
                import logging
                logging.error(f"Alpaca entegrasyon hatası (Dashboard): {e}")

    # Fallback (Simülasyon Modu)
    live_trade_manager.get_live_prices()
    active_list = [p for p in live_trade_manager.positions.values() if p.status == "OPEN"]
    return {
        "account_balance": round(live_trade_manager.account_balance, 2),
        "available_cash": round(live_trade_manager.available_cash, 2),
        "total_commissions_paid": round(live_trade_manager.total_commissions_paid, 2),
        "active_positions": active_list,
        "history": live_trade_manager.trade_history[:10]
    }

@router.post("/open")
async def open_live_position(req: OpenPositionRequest):
    """
    1-Tıkla Canlı Pozisyon Açılışı (Alpaca Broker Destekli)
    """
    if settings.trading_mode in ["LIVE", "PAPER"]:
        from services.broker.factory import get_broker
        broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
        if broker and broker.api:
            # Hızlı hesaplama: anlık fiyatı tradingview feed'den al
            live_trade_manager.get_live_prices()
            curr_price = live_trade_manager.market_prices.get(req.symbol.upper(), {}).get("price", 0)
            if curr_price > 0:
                qty = round(req.capital / curr_price, 4)
                tp_price = curr_price * (1 + (req.tp_pct / 100.0))
                sl_price = curr_price * (1 - (req.sl_pct / 100.0))
                
                res = broker.place_bracket_order(req.symbol, req.side, qty, tp_price, sl_price)
                if res.get("status") == "success":
                    return res
            
    # Fallback to local
    return live_trade_manager.open_position(
        symbol=req.symbol,
        capital=req.capital,
        side=req.side,
        tp_pct=req.tp_pct,
        sl_pct=req.sl_pct
    )

@router.post("/close/{pos_id}")
async def close_live_position(pos_id: str):
    """
    1-Tıkla Canlı Pozisyon Kapatma (Alpaca Broker Destekli)
    """
    if settings.trading_mode in ["LIVE", "PAPER"]:
        from services.broker.factory import get_broker
        broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
        if broker and broker.api:
            # Eğer Alpaca pozisyonu kapatılmak isteniyorsa pos_id veya symbol olabilir.
            # Alpaca close_position() methodu symbol bekler. Dashboard id veya symbol gönderebilir.
            # pos_id'de symbol varsa onu parse edelim (örn: POS-NVDA -> NVDA)
            symbol = pos_id.split("-")[1] if "POS-" in pos_id else pos_id
            res = broker.close_position(symbol)
            if res.get("status") == "success":
                return {"status": "success", "closed_position": res}

    res = live_trade_manager.close_position(pos_id, "MANUAL_CLOSE")
    if not res:
        return JSONResponse(status_code=404, content={"error": "Pozisyon bulunamadı veya zaten kapalı"})
    return {"status": "success", "closed_position": res}

@router.post("/reset-account")
async def reset_account_balance():
    """
    Kasayı Kesin Olarak $1,000.00 Tabanına Sıfırlar ve Tüm Eski İşlem Kalıntılarını Temizler
    """
    live_trade_manager.reset_account()
    from services.engine.experience_memory_engine import experience_memory_engine
    experience_memory_engine.reset_memory()
    return {
        "status": "success",
        "account_balance": live_trade_manager.total_account_equity,
        "cash_balance": live_trade_manager.available_cash,
        "message": "Kasa bakiyesi kesin olarak $1,000.00 tabanına sıfırlandı."
    }

@router.get("/daily-stats")
async def get_daily_stats():
    """
    Alpaca komisyonları dahil günlük PnL (Kâr/Zarar) istatistikleri
    """
    return live_trade_manager.daily_stats


@router.get("/clock")
async def get_alpaca_clock():
    """
    Alpaca'dan canlı piyasa saati ve durumunu çeker
    """
    if settings.trading_mode in ["LIVE", "PAPER"]:
        from services.broker.factory import get_broker
        broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
        if broker and broker.api:
            try:
                clock = broker.api.get_clock()
                return {
                    "status": "success",
                    "is_open": clock.is_open,
                    "timestamp": clock.timestamp.isoformat(),
                    "next_open": clock.next_open.isoformat(),
                    "next_close": clock.next_close.isoformat()
                }
            except Exception as e:
                import logging
                logging.error(f"Alpaca clock fetch error: {e}")
                
    # Fallback to local time
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "status": "fallback",
        "is_open": True,  # Mocked
        "timestamp": now.isoformat(),
        "next_open": now.isoformat(),
        "next_close": now.isoformat()
    }

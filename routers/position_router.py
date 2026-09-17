import time
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from services.market_feed.live_stream import live_trade_manager, ActivePosition
from core.config import settings
from core.logger import logger
from core.security import verify_ip


router = APIRouter(dependencies=[Depends(verify_ip)])

# 15 saniyelik pozisyon cache — Alpaca API her cagride sorgulanmaz
_pos_cache = {"data": None, "ts": 0}
_POS_CACHE_TTL = 15


class OpenPositionRequest(BaseModel):
    symbol: str = Field("NVDA", description="Sembol")
    capital: float = Field(100.0, description="Kullanılacak Sermaye ($ / ₺)")
    side: str = Field("BUY", description="BUY veya SELL")
    tp_pct: float = Field(3.0, description="Kâr Al Yüzdesi")
    sl_pct: float = Field(1.5, description="Zarar Kes Yüzdesi")

class AutoTradeToggleRequest(BaseModel):
    enabled: bool = Field(..., description="Tam Otonom Mod Durumu")

@router.post("/toggle-auto-trade")
async def toggle_auto_trade(req: AutoTradeToggleRequest):
    from services.market_feed.live_stream import live_trade_manager
    live_trade_manager.auto_trade_enabled = req.enabled
    status_str = "AÇIK" if req.enabled else "KAPALI"
    return {"status": "success", "message": f"Tam Otonom Mod {status_str} konuma getirildi."}


@router.get("/active")
async def get_active_positions():
    """
    Canli Acik Pozisyonlar ve Kar/Zarar Listesi (15s cache ile)
    """
    global _pos_cache
    now = time.time()
    if _pos_cache["data"] is not None and (now - _pos_cache["ts"]) < _POS_CACHE_TTL:
        return _pos_cache["data"]

    if settings.trading_mode in ["LIVE", "PAPER"]:
        from services.broker.factory import get_broker
        broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
        if broker and broker.api:
            try:

                # Canlı bakiye ve pozisyonları çek
                # Kullanıcı talebi: Gerçek Alpaca bütçesi akışa yansıtılmalı.
                try:
                    alpaca_eq = float(broker.get_account_balance())
                    
                    raw_positions = broker.get_open_positions()
                    active_assets = sum(float(p.get("market_value", 0)) for p in raw_positions)
                    
                    effective_balance = float(alpaca_eq)
                    real_available_cash = max(0.0, effective_balance - active_assets)
                except Exception as e:
                    effective_balance = live_trade_manager.total_account_equity
                    real_available_cash = live_trade_manager.available_cash
                    raw_positions = []
                
                active_list = []
                for p in raw_positions:
                    sym = p.get("symbol")
                    local_pos = next((lp for lp in live_trade_manager.positions.values() if lp.symbol == sym and lp.status == "OPEN"), None)
                    opened_at_val = local_pos.opened_at if local_pos else "Senkronize"

                    entry_price = float(p.get("avg_entry_price") or 0.0)
                    side = "BUY" if p.get("side") == "long" else "SELL"
                    qty = float(p.get("qty") or 0.0)
                    
                    # === FİYAT KAYNAĞI: Alpaca GERCEK ZAMANLI — TV fallback ===
                    # Alpaca'nın current_price'ı broker'dan direkt gelen en güncel fiyattır.
                    # TradingView fiyatı sadece Alpaca yoksa VEYA 90s'den tazeyse kullanılır.
                    alpaca_curr_price = float(p.get("current_price") or 0.0)
                    tv_price = 0.0
                    tv_is_fresh = False

                    # Sembol uyumluluğu kontrolü (PAXGUSD → PAXGUSDT gibi)
                    tv_sym = sym or ""
                    if tv_sym.endswith("USD") and tv_sym != "USD":
                        tv_sym = tv_sym.replace("USD", "USDT")

                    # TV fiyatı tazeyse (< 90s) al
                    if tv_sym in live_trade_manager.market_prices:
                        tv_entry = live_trade_manager.market_prices[tv_sym]
                        tv_price = tv_entry.get("price", 0.0)
                        last_ts  = tv_entry.get("last_updated_ts", 0)
                        import time as _time
                        tv_is_fresh = (last_ts > 0 and (_time.time() - last_ts) < 90)

                    # Öncelik: Alpaca > TV (TV sadece Alpaca yoksa ve tazeyse)
                    if alpaca_curr_price > 0:
                        final_current_price = alpaca_curr_price   # ✅ Her zaman Alpaca önce
                    elif tv_price > 0 and tv_is_fresh:
                        final_current_price = tv_price            # Fallback: TV taze ise
                    elif tv_price > 0:
                        final_current_price = tv_price            # Son çare: TV stale ama Alpaca yok
                    else:
                        final_current_price = 0.0


                    
                    # PnL'yi yeni fiyata göre baştan hesapla
                    real_pnl = 0.0
                    real_pnl_pct = 0.0
                    if entry_price > 0 and final_current_price > 0:
                        if side == "BUY":
                            real_pnl = (final_current_price - entry_price) * qty
                            real_pnl_pct = (final_current_price - entry_price) / entry_price * 100
                        else:
                            real_pnl = (entry_price - final_current_price) * qty
                            real_pnl_pct = (entry_price - final_current_price) / entry_price * 100
                    
                    tp_price = 0.0
                    sl_price = 0.0
                    
                    if local_pos:
                        tp_price = local_pos.target_profit_price
                        sl_price = local_pos.stop_loss_price
                        # Alpaca'dan gelen güncel fiyatı yerel pozisyona da yansıt (Senkronize kalsın)
                        local_pos.current_price = final_current_price
                    elif entry_price > 0:
                        dyn_tp_pct, dyn_sl_pct = 3.5, 1.75
                        try:
                            from services.engine.experience_memory_engine import experience_memory_engine
                            if hasattr(experience_memory_engine, "get_dynamic_margins"):
                                dyn_tp_pct, dyn_sl_pct = experience_memory_engine.get_dynamic_margins(sym)
                        except Exception:
                            pass
                            
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
                        "current_price": final_current_price,
                        "quantity": qty,
                        "nominal_value": final_current_price * qty if final_current_price > 0 else float(p.get("market_value") or 0.0),
                        "target_profit_price": round(tp_price, 4),
                        "stop_loss_price": round(sl_price, 4),
                        "unrealized_pnl": float(real_pnl if tv_price > 0 else (p.get("unrealized_pl") or 0.0)),
                        "unrealized_pnl_pct": float(real_pnl_pct if tv_price > 0 else float(p.get("unrealized_plpc") or 0.0) * 100),
                        "opened_at": opened_at_val,
                        "status": "OPEN"
                    })
                
                # real_available_cash already fetched from broker above
                
                result = {
                    "account_balance": round(effective_balance, 2),
                    "available_cash": round(real_available_cash, 2),
                    "total_commissions_paid": round(live_trade_manager.total_commissions_paid + sum(p.commission_fees for p in live_trade_manager.positions.values() if p.status == "OPEN"), 2),
                    "active_positions": active_list,
                    "history": live_trade_manager.trade_history[:10]
                }
                _pos_cache["data"] = result
                _pos_cache["ts"] = time.time()
                return result
            except Exception as e:
                import logging
                logging.error(f"Alpaca entegrasyon hatası (Dashboard): {e}")

    # Fallback (Simülasyon Modu)
    live_trade_manager.get_live_prices()
    active_list = [p for p in live_trade_manager.positions.values() if p.status == "OPEN"]
    result = {
        "account_balance": round(live_trade_manager.account_balance, 2),
        "available_cash": round(live_trade_manager.available_cash, 2),
        "total_commissions_paid": round(live_trade_manager.total_commissions_paid + sum(p.commission_fees for p in live_trade_manager.positions.values() if p.status == "OPEN"), 2),
        "active_positions": active_list,
        "history": live_trade_manager.trade_history[:10]
    }
    _pos_cache["data"] = result
    _pos_cache["ts"] = time.time()
    return result

@router.post("/open")
async def open_live_position(req: OpenPositionRequest):
    """
    1-Tıkla Canlı Pozisyon Açılışı (Alpaca Broker Destekli)
    """
    try:
        from services.broker.alpaca_client import alpaca_client

        # 1. Anlık fiyatı al (lokalde yoksa Alpaca'dan çek)
        # NORMALIZE SYMBOL
        req_sym = req.symbol.upper()
        if req_sym.endswith("USD") and req_sym != "USD":
            req_sym += "T"

        curr_price = live_trade_manager.market_prices.get(req_sym, {}).get("price", 0)
        if curr_price == 0:
            curr_price = alpaca_client.get_current_price(req_sym)
            
        if curr_price == 0:
            return {"status": "error", "message": f"{req.symbol} için canlı fiyat alınamadı."}

        # 2. Her zaman lokal canlı yönetim motoruna (Dashboard için) pozisyon açtır
        pos = live_trade_manager.open_position(
            symbol=req_sym,
            capital=req.capital,
            side=req.side,
            tp_pct=req.tp_pct,
            sl_pct=req.sl_pct,
            entry_price_override=curr_price
        )
        
        if not pos:
            return {"status": "error", "message": "Yetersiz bütçe, makro koruma aktif veya maksimum açık işlem limitine ulaşıldı."}

        return {"status": "success", "position": pos.dict()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Server error: {str(e)}"}

@router.post("/close/{pos_id:path}")
async def close_live_position(pos_id: str):
    """
    1-Tikla Canli Pozisyon Kapatma (Alpaca Broker Destekli)
    Alpaca basarisiz olsa bile yerel pozisyon her zaman kapatilir.
    """
    # pos_id formatlarini normalize et:
    # "POS-COIN" -> "COIN"
    # "POS-COIN-20241231" -> "COIN"
    # "COIN" -> "COIN"
    parts = pos_id.split("-")
    if parts[0] == "POS" and len(parts) >= 2:
        symbol = parts[1]
    else:
        symbol = pos_id

    alpaca_ok = False
    alpaca_msg = ""

    # 1. Alpaca'da kapat (piyasa kapali veya hata olsa bile devam et)
    if settings.trading_mode in ["LIVE", "PAPER"]:
        try:
            from services.broker.factory import get_broker
            broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
            if broker and broker.api:
                res = broker.close_position(symbol)
                if res.get("status") == "success":
                    alpaca_ok = True
                    logger.info(f"[MANUEL KAPAT] {symbol} Alpaca'da kapatildi.")
                else:
                    alpaca_msg = res.get("message", "Alpaca hatasi")
                    logger.warning(f"[MANUEL KAPAT] {symbol} Alpaca hatasi: {alpaca_msg}. Yerel kapatma yapiliyor.")
        except Exception as e:
            alpaca_msg = str(e)
            logger.warning(f"[MANUEL KAPAT] {symbol} Alpaca exception: {e}. Yerel kapatma yapiliyor.")

    # 2. Yerel pozisyonu MUTLAKA kapat (Alpaca basarisiz olsa da)
    # Once direkt pos_id ile dene, bulamazsa symbol uzerinden tara
    local_res = live_trade_manager.close_position(pos_id, "MANUAL_CLOSE")

    if not local_res:
        # pos_id eşleşmedi — sembol üzerinden tara
        matched_pos_id = None
        for pid, pos in live_trade_manager.positions.items():
            if pos.symbol == symbol and pos.status == "OPEN":
                matched_pos_id = pid
                break
        if matched_pos_id:
            local_res = live_trade_manager.close_position(matched_pos_id, "MANUAL_CLOSE")

    if not local_res:
        return JSONResponse(status_code=404, content={
            "error": f"Pozisyon bulunamadi: {pos_id}",
            "alpaca_status": "success" if alpaca_ok else f"error: {alpaca_msg}",
            "tip": "Pozisyon zaten kapali olabilir veya ID formati hatali."
        })

    return {
        "status": "success",
        "closed_position": local_res,
        "alpaca_synced": alpaca_ok,
        "alpaca_note": alpaca_msg if not alpaca_ok else ""
    }


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
        "message": "Kasa bakiyesi Alpaca üzerinden güncellenerek sıfırlandı."
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

@router.get("/history/summary")
async def get_history_summary():
    """Returns a summary and list of all historically closed positions."""
    from services.market_feed.live_stream import live_trade_manager
    history = live_trade_manager.trade_history
    
    total_real = 0
    total_virtual = 0
    winning_real = 0
    winning_virtual = 0
    pnl_real = 0.0
    pnl_virtual = 0.0
    
    # Kullanıcı Tanımı: 
    # Gerçek (Manuel) = Kullanıcının kendi eliyle kapattığı (MANUAL_CLOSE, CLOSED_OFFLINE_SYNC)
    # Sanal (Otonom) = Botun kendi kendine kapattığı (CLOSED_FLASH_CRASH, CLOSED_SL, CLOSED_TP, CLOSED_TRAILING, SHADOW_CLOSED vb.)
    
    manual_reasons = {
        "MANUAL_CLOSE", "CLOSED_OFFLINE_SYNC", "OFFLINE_SYNC", "MANUAL_SYNC"
    }
    
    # Calculate stats
    for trade in history:
        pnl = float(trade.get("net_pnl", 0.0))
        reason = trade.get("reason", "")
        
        is_manual = reason in manual_reasons
        
        if not is_manual:
            total_virtual += 1
            pnl_virtual += pnl
            if pnl > 0: winning_virtual += 1
        else:
            total_real += 1
            pnl_real += pnl
            if pnl > 0: winning_real += 1
            
    win_rate_real = (winning_real / total_real * 100) if total_real > 0 else 0.0
    win_rate_virtual = (winning_virtual / total_virtual * 100) if total_virtual > 0 else 0.0
    
    # "Gerçek (Manuel) / Sanal (Otonom)" şeklinde frontend'e string olarak dön
    total_trades_str = f"{total_real} / {total_virtual}"
    win_rate_str = f"%{round(win_rate_real, 1)} / %{round(win_rate_virtual, 1)}"
    
    # PnL Renkleri için ham verileri de dönelim, string'i frontend halletsin
    return {
        "total_trades": total_trades_str,
        "win_rate": win_rate_str,
        "pnl_real": round(pnl_real, 2),
        "pnl_virtual": round(pnl_virtual, 2),
        "recent_trades": history[:30] # Return up to 30 most recent for the UI table
    }

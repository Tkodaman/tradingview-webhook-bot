import time
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from services.market_feed.live_stream import live_trade_manager, ActivePosition
from core.config import settings
from core.logger import logger
from core.security import verify_ip


router = APIRouter(dependencies=[Depends(verify_ip)])

# 3 saniyelik pozisyon cache
_pos_cache = {"data": None, "ts": 0}
_POS_CACHE_TTL = 3

_ai_summary_cache = {"text": "Veri sentezleniyor... İlk 10 işlemden sonra aktifleşecek.", "ts": 0}
_AI_SUMMARY_TTL = 600  # 10 dakikada bir güncelle

import threading
from services.ai.llm_master_agent import LLMMasterAgentService
_llm_agent = LLMMasterAgentService()

def _update_ai_summary_bg(history_sample):
    global _ai_summary_cache
    try:
        if not history_sample:
            return
        
        prompt = "Sen elit bir hedge fon yöneticisisin. Aşağıdaki son kapatılan işlemlere bakarak 2 cümlelik agresif ve teknik bir özet yap. Neden kazandık/kaybettik? Botun performansı nasıl?\n\nİşlemler:\n"
        for t in history_sample:
            prompt += f"- {t.get('symbol')} | PnL: {t.get('net_pnl')} | Sebep: {t.get('reason')}\n"
            
        res = _llm_agent.chat(prompt, max_tokens=150)
        if "[LLM_ERROR]" not in res and "[LLM_OFFLINE]" not in res:
            _ai_summary_cache["text"] = res
            _ai_summary_cache["ts"] = time.time()
    except Exception as e:
        logger.error(f"[AI SUMMARY ERROR] {e}")


class OpenPositionRequest(BaseModel):
    symbol: str = Field("NVDA", description="Sembol")
    capital: float = Field(100.0, description="Kullanılacak Sermaye ($ / ₺)")
    side: str = Field("BUY", description="BUY veya SELL")
    tp_pct: float = Field(3.0, description="Kâr Al Yüzdesi")
    sl_pct: float = Field(1.5, description="Zarar Kes Yüzdesi")

class AutoTradeToggleRequest(BaseModel):
    enabled: bool = Field(..., description="Tam Otonom Mod Durumu")

@router.post("/toggle-auto-trade")
def toggle_auto_trade(req: AutoTradeToggleRequest):
    from services.market_feed.live_stream import live_trade_manager
    live_trade_manager.auto_trade_enabled = req.enabled
    live_trade_manager.save_auto_trade_flag()
    status_str = "AÇIK" if req.enabled else "KAPALI"
    return {"status": "success", "message": f"Tam Otonom Mod {status_str} konuma getirildi."}


@router.get("/active")
def get_active_positions():
    """
    Canli Acik Pozisyonlar ve Kar/Zarar Listesi (15s cache ile)
    """
    global _pos_cache
    now = time.time()
    if _pos_cache["data"] is not None and (now - _pos_cache["ts"]) < _POS_CACHE_TTL:
        return _pos_cache["data"]

    from services.engine.ha_manager import ha_manager
    if not ha_manager.is_leader:
        live_trade_manager.load_state()

    # STAMPEDE KORUMASI (Stale-while-revalidate): 
    # API yavaşsa diğer isteklerin beklemesi yerine eski veriyi almasını sağla
    if _pos_cache["data"] is not None:
        _pos_cache["ts"] = now + 15 # Geçici olarak 15 sn uzat, böylece diğer istekler eski veriyi kullanır

    if settings.trading_mode in ["LIVE", "PAPER"]:
        from services.broker.factory import get_broker
        broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
        if broker and broker.api:
            try:

                api_health = {"binance": False, "alpaca": False}
                
                # Canlı bakiye ve pozisyonları çek
                # Kullanıcı talebi: Gerçek Alpaca bütçesi akışa yansıtılmalı.
                try:
                    alpaca_eq = float(broker.get_account_balance())
                    
                    raw_positions = broker.get_open_positions()
                    active_assets = sum(float(p.get("market_value", 0)) for p in raw_positions)
                    
                    effective_balance = float(alpaca_eq)
                    real_available_cash = max(0.0, effective_balance - active_assets)
                    api_health["alpaca"] = True
                except Exception as e:
                    effective_balance = live_trade_manager.total_account_equity
                    real_available_cash = live_trade_manager.available_cash
                    raw_positions = []
                
                # BİNANCE BAĞLANTI KONTROLÜ (API HEALTH)
                binance_live_prices = {}
                try:
                    from services.broker.factory import get_broker
                    b_broker = get_broker("BINANCE", paper=(settings.trading_mode == "PAPER"))
                    if b_broker and getattr(b_broker, "client", None) is not None:
                        api_health["binance"] = True
                        
                        crypto_syms = []
                        for p in live_trade_manager.positions.values():
                            if p.status == "OPEN" and p.market == "CRYPTO":
                                crypto_syms.append(p.symbol.replace("BINANCE:", "").replace("CRYPTO:", ""))
                        
                        if crypto_syms:
                            binance_live_prices = getattr(b_broker, "get_realtime_prices", lambda x: {})(crypto_syms)
                except:
                    pass
                
                # Alpaca'daki pozisyon sembollerini takip et
                alpaca_symbols = set()
                for p in raw_positions:
                    p_sym = (p.get("symbol") or "").upper()
                    alpaca_symbols.add(p_sym)
                    if p_sym.endswith("USD") and p_sym != "USD":
                        alpaca_symbols.add(p_sym.replace("USD", "USDT"))
                    
                # Eğer yerel (PAPER) açık pozisyonlar varsa ve Alpaca'da yoksa, onları raw_positions'a ekle
                # live_trade_manager.positions dictionary'sinde key pos_id'dir.
                
                # BİNANCE BAKİYESİNİ ÇEK (Artık API'den ham bakiye değil, 1200$'lık izole bütçeden kalanı dinamik göstereceğiz)
                # (API çağrısı kaldırılarak hızlandırıldı)
                
                for pos_id, lp in live_trade_manager.positions.items():
                    local_sym = (lp.symbol or "").upper()
                    # Tüm pozisyonları göster, sembol bazlı filtreleme (tekilleştirme) yapma.
                    # Ayrıca Alpaca'da aynı sembol var diye Binance (CRYPTO) pozisyonunu gizleme.
                    is_alpaca_overlap = (lp.market != "CRYPTO") and (local_sym in alpaca_symbols)
                    if lp.status == "OPEN" and not is_alpaca_overlap:
                        # Yerel pozisyonu Alpaca formatında hazırla (Paper Trading)
                        local_p = {
                            "id": lp.id,
                            "symbol": lp.symbol,
                            "asset_class": lp.market,
                            "side": "long" if lp.side == "BUY" else "short",
                            "avg_entry_price": str(lp.entry_price),
                            "qty": str(lp.quantity),
                            "current_price": str(lp.current_price or lp.entry_price),
                            "market_value": str(lp.nominal_value),
                            "unrealized_pl": str(lp.unrealized_pnl),
                            "unrealized_plpc": str(lp.unrealized_pnl_pct / 100.0)
                        }
                        raw_positions.append(local_p)
                
                active_list = []
                for p in raw_positions:
                    sym = p.get("symbol") or ""
                    # Sembol uyumluluğu kontrolü (PAXGUSD → PAXGUSDT gibi)
                    tv_sym = sym
                    if tv_sym.endswith("USD") and tv_sym != "USD":
                        tv_sym = tv_sym.replace("USD", "USDT")
                    
                    # Alpaca symbol could be BTC/USD, tv_sym is BTC/USDT. Local might be BINANCE:BTCUSDT.
                    # We match if local symbol ends with tv_sym or matches sym.
                    clean_sym = sym.upper().replace("BINANCE:", "").replace("CRYPTO:", "")
                    clean_tv_sym = tv_sym.upper().replace("BINANCE:", "").replace("CRYPTO:", "")
                    local_pos = None
                    for lp in live_trade_manager.positions.values():
                        if lp.status == "OPEN":
                            clean_lp = lp.symbol.upper().replace("BINANCE:", "").replace("CRYPTO:", "")
                            if clean_lp in [clean_sym, clean_tv_sym]:
                                local_pos = lp
                                break
                    
                    if local_pos and local_pos.opened_at:
                        opened_at_val = local_pos.opened_at
                    else:
                        from datetime import datetime, timezone
                        opened_at_val = datetime.now(timezone.utc).isoformat()

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

                    # YENİ ÖNCELİK: Alpaca API her zaman öncelikli (Web UI ile birebir eşleşmesi için)
                    # TradingView free plan 15 dakika gecikmeli veri verdiğinden, Alpaca PnL'ini kullan.
                    
                    binance_price = 0.0
                    if clean_sym in binance_live_prices:
                        if isinstance(binance_live_prices[clean_sym], dict):
                            binance_price = binance_live_prices[clean_sym].get("price", 0.0)
                        elif isinstance(binance_live_prices[clean_sym], (float, int)):
                            binance_price = float(binance_live_prices[clean_sym])

                    if binance_price > 0:
                        final_current_price = binance_price       # ✅ Canlı Binance önceliği
                    elif alpaca_curr_price > 0:
                        final_current_price = alpaca_curr_price   # ✅ Sonra Alpaca PnL
                    elif tv_price > 0 and tv_is_fresh:
                        final_current_price = tv_price            # Fallback: TV taze
                    elif tv_price > 0:
                        final_current_price = tv_price            # Son çare: TV stale
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
                    
                    # Trailing stop ve break-even durumu — yerel pozisyondan al
                    trailing_active = False
                    break_even_active = False
                    highest_seen = 0.0
                    
                    if local_pos:
                        tp_price = local_pos.target_profit_price
                        sl_price = local_pos.stop_loss_price
                        trailing_active = bool(local_pos.trailing_stop_activated)
                        break_even_active = bool(local_pos.break_even_activated)
                        highest_seen = float(local_pos.highest_price_seen or 0.0)
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
                            
                            
                    # Pydantic ActivePosition dict objesinden 'market' bilgisini al (Yoksa asset_class'a düş)
                    market_class = str(p.get("market") or p.get("asset_class", "STOCK")).upper()
                    session_badge = ""
                    if market_class != "CRYPTO":
                        from services.risk_engine.market_hours import market_hours_validator
                        _is_open, _msg, _details = market_hours_validator.is_market_open(sym)
                        if _details.get("session") == "PRE_MARKET":
                            session_badge = "PRE"
                        elif _details.get("session") == "POST_MARKET":
                            session_badge = "POST"
                        elif not _is_open:
                            session_badge = "KAPALI"
                            
                    pos_id_to_send = local_pos.id if local_pos else f"POS-{sym}"
                    active_list.append({
                        "id": pos_id_to_send,
                        "symbol": sym,
                        "market": market_class,
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
                        "status": "OPEN",
                        "session_badge": session_badge,
                        "is_manual": getattr(local_pos, "is_manual", (True if local_pos and hasattr(local_pos, "reason") and local_pos.reason and "MANUAL" in str(local_pos.reason).upper() else False)) if local_pos else False,
                        "source": "MANUEL" if (getattr(local_pos, "is_manual", False) or (local_pos and hasattr(local_pos, "reason") and local_pos.reason and "MANUAL" in str(local_pos.reason).upper())) else getattr(local_pos, "source", "OTONOM"),
                        # Trailing / Break-Even durumu (dashboard göstergesi için)
                        "trailing_stop_activated": trailing_active,
                        "break_even_activated": break_even_active,
                        "highest_price_seen": round(highest_seen, 5)
                    })
                
                # real_available_cash already fetched from broker above
                
                # Calculate Binance Dynamic Budget and Commissions
                crypto_realized = sum(float(t.get("net_pnl", 0.0) or 0.0) for t in live_trade_manager.trade_history if t.get("market") == "CRYPTO" and t.get("reason") not in ["CLOSED_OFFLINE_SYNC", "SIMULATION_CLOSE"])
                crypto_comm = sum(float(t.get("alpaca_commission", 0.0) or 0.0) for t in live_trade_manager.trade_history if t.get("market") == "CRYPTO" and t.get("reason") not in ["CLOSED_OFFLINE_SYNC", "SIMULATION_CLOSE"])
                alpaca_comm = sum(float(t.get("alpaca_commission", 0.0) or 0.0) for t in live_trade_manager.trade_history if t.get("market") != "CRYPTO" and t.get("reason") not in ["CLOSED_OFFLINE_SYNC", "SIMULATION_CLOSE"])
                
                binance_budget_limit = float(getattr(settings, "crypto_paper_budget", 1600.0)) + crypto_realized - crypto_comm
                crypto_invested = sum(p.nominal_value for p in live_trade_manager.positions.values() if p.status == "OPEN" and p.market == "CRYPTO")
                binance_cash = max(0.0, binance_budget_limit - crypto_invested)
                
                result = {
                    "account_balance": round(effective_balance, 2),
                    "available_cash": round(real_available_cash, 2),
                    "total_commissions_paid": round(alpaca_comm, 2), # Legacy backward compatibility
                    "alpaca_commission": round(alpaca_comm, 2),
                    "binance_commission": round(crypto_comm, 2),
                    "binance_cash": round(binance_cash, 2),
                    "binance_budget_limit": round(binance_budget_limit, 2),
                    "active_positions": active_list,
                    "history": live_trade_manager.trade_history[:10],
                    "trading_mode": settings.trading_mode,
                    "api_health": api_health
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
        "alpaca_commission": 0.0,
        "binance_commission": 0.0,
        "binance_cash": round(live_trade_manager.available_cash, 2),
        "binance_budget_limit": settings.crypto_paper_budget,
        "active_positions": active_list,
        "history": live_trade_manager.trade_history[:10],
        "trading_mode": settings.trading_mode,
        "api_health": {"binance": False, "alpaca": False}
    }
    _pos_cache["data"] = result
    _pos_cache["ts"] = time.time()
    return result

@router.post("/open")
async def open_live_position(req: OpenPositionRequest):
    """
    1-Tıkla Canlı Pozisyon Açılışı (Alpaca Broker Destekli)
    """
    import asyncio
    try:
        from services.broker.alpaca_client import alpaca_client

        # 1. Anlık fiyatı al (lokalde yoksa Alpaca'dan çek)
        # NORMALIZE SYMBOL
        req_sym = req.symbol.upper()
        if req_sym.endswith("USD") and req_sym != "USD":
            req_sym += "T"

        curr_price = live_trade_manager.market_prices.get(req_sym, {}).get("price", 0)
        if curr_price == 0:
            # Blocking API çağrısını thread'e taşı - event loop bloklanmasın
            curr_price = await asyncio.to_thread(alpaca_client.get_current_price, req_sym)
            
        if curr_price == 0:
            # Fallback to Binance API for Crypto
            try:
                import requests
                binance_sym = req_sym if req_sym.endswith("USDT") else f"{req_sym}USDT"
                res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={binance_sym}", timeout=3)
                if res.status_code == 200:
                    curr_price = float(res.json()["price"])
            except Exception:
                pass
                
        if curr_price == 0:
            return {"status": "error", "message": f"{req.symbol} için canlı fiyat alınamadı (Sembolü USDT ile biten şekilde yazın, örn: NEARUSDT)."}

        import functools
        open_func = functools.partial(
            live_trade_manager.open_position,
            symbol=req_sym,
            capital=req.capital,
            side=req.side,
            tp_pct=req.tp_pct,
            sl_pct=req.sl_pct,
            entry_price_override=curr_price,
            is_manual=True
        )
        pos = await asyncio.to_thread(open_func)
        
        if not pos:
            return {"status": "error", "message": "Emir reddedildi! Bütçe/Koruma veya Alpaca API Hatası. Tam sebep için Kayan Yazı loguna bakın!"}

        return {"status": "success", "position": pos.model_dump()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Server error: {str(e)}"}

@router.post("/close/{pos_id:path}")
def close_live_position(pos_id: str):
    """
    1-Tikla Canli Pozisyon Kapatma (Alpaca Broker Destekli)
    Alpaca basarisiz olsa bile yerel pozisyon her zaman kapatilir.
    """
    # pos_id formatlarini normalize et:
    # "POS-COIN" -> "COIN"
    # "POS-COIN-20241231" -> "COIN"
    # "COIN" -> "COIN"
    parts = pos_id.split("_") if pos_id.startswith("sync_") else pos_id.split("-")
    if pos_id.startswith("POS-") and len(parts) >= 2:
        symbol = parts[1]
    elif pos_id.startswith("sync_") and len(parts) >= 3:
        symbol = parts[2]
    else:
        symbol = pos_id

    alpaca_ok = False
    alpaca_msg = ""
    
    # Yerel kapatma (Alpaca / Binance fark etmeksizin her zaman yapılmalı!)
    # Once direkt pos_id ile dene, bulamazsa symbol uzerinden tara
    local_res = live_trade_manager.close_position(pos_id, "MANUAL_CLOSE")

    matched_pos_id = pos_id
    if not local_res:
        # pos_id eşleşmedi — sembol üzerinden tara
        clean_target_sym = symbol.upper().replace("BINANCE:", "").replace("CRYPTO:", "")
        for pid, pos in live_trade_manager.positions.items():
            clean_pos_sym = pos.symbol.upper().replace("BINANCE:", "").replace("CRYPTO:", "")
            if clean_pos_sym == clean_target_sym and pos.status in ["OPEN", "PENDING_CLOSE"]:
                matched_pos_id = pid
                local_res = live_trade_manager.close_position(pid, "MANUAL_CLOSE")
                break

    # Kapatma sonucu kontrol et. Eğer PENDING_CLOSE olduysa (Market Kapalı), bu bir hatadır değil başarıdır!
    current_pos = live_trade_manager.positions.get(matched_pos_id)
    if not local_res:
        if current_pos and current_pos.status == "PENDING_CLOSE":
            return {
                "status": "success",
                "message": "Kapatma emri borsaya iletildi ancak piyasa kapalı olduğu için sıraya alındı (Queued).",
                "closed_position": None,
                "alpaca_synced": True
            }
        
        return JSONResponse(status_code=404, content={
            "error": f"Pozisyon bulunamadi: {pos_id}",
            "tip": "Pozisyon zaten kapali olabilir veya ID formati hatali."
        })

    return {
        "status": "success",
        "closed_position": local_res,
        "alpaca_synced": True,
        "alpaca_note": ""
    }

@router.post("/close_all")
def close_all_active_positions():
    """
    Acil durum (Panik) anında veya Nükleer Çekilme (Retreat) komutuyla
    tüm açık (OPEN) pozisyonları piyasa fiyatından kapatır.
    """
    from services.market_feed.live_stream import live_trade_manager
    active_positions = [pid for pid, p in live_trade_manager.positions.items() if p.status == "OPEN"]
    
    closed_count = 0
    errors = []
    
    for pid in active_positions:
        try:
            # call existing close function internally
            close_live_position(pid)
            closed_count += 1
        except Exception as e:
            errors.append(f"{pid}: {str(e)}")
            
    return {
        "status": "success",
        "message": f"{closed_count} adet pozisyon basariyla kapatildi.",
        "errors": errors
    }

@router.post("/lock_profits")
def lock_all_profits():
    """
    Açık olan ve anlık PnL'i kârda olan ( > %0.5 ) tüm pozisyonların
    Zarar Kes (Stop-Loss) seviyelerini komisyonu kurtaracak şekilde
    Giriş Fiyatının %0.2 üstüne çeker (Break-Even).
    Böylece pozisyonlar risksiz hale (Risk-Free) gelir.
    """
    from services.market_feed.live_stream import live_trade_manager
    locked_count = 0
    
    for pid, pos in live_trade_manager.positions.items():
        if pos.status == "OPEN":
            # Guncel kar hesaplamasi
            if pos.entry_price > 0 and pos.current_price > 0:
                pct = ((pos.current_price - pos.entry_price) / pos.entry_price) * 100.0
                if pos.side == "SELL":
                    pct = -pct
                    
                # Sadece %0.5'ten fazla karda olanlara mudahale et
                if pct > 0.5:
                    if pos.side == "BUY":
                        new_sl = pos.entry_price * 1.002 # %0.2 komisyon kurtarma marji
                        if new_sl > pos.stop_loss_price:
                            pos.stop_loss_price = new_sl
                            locked_count += 1
                    else: # SELL
                        new_sl = pos.entry_price * 0.998
                        if new_sl < pos.stop_loss_price or pos.stop_loss_price == 0:
                            pos.stop_loss_price = new_sl
                            locked_count += 1
                            
                    # API guncellemesi (Broker)
                    try:
                        from services.broker.factory import get_broker
                        b_name = "BINANCE" if pos.market == "CRYPTO" else "ALPACA"
                        broker = get_broker(b_name)
                        broker.update_bracket_orders(pos.symbol, take_profit_price=pos.target_profit_price, stop_loss_price=pos.stop_loss_price)
                    except Exception:
                        pass
                        
    live_trade_manager.save_state()
    return {
        "status": "success",
        "message": f"{locked_count} adet varligin Stop-Loss'u 'Break-Even' (Kar Koruma) moduna alindi."
    }

@router.post("/reset-account")
def reset_account_balance():
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
def get_daily_stats():
    """
    Alpaca komisyonları dahil günlük PnL (Kâr/Zarar) istatistikleri
    """
    return live_trade_manager.daily_stats


@router.get("/clock")
def get_alpaca_clock():
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
def get_history_summary():
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
    
    # AI Summary Background Trigger
    global _ai_summary_cache
    if time.time() - _ai_summary_cache["ts"] > _AI_SUMMARY_TTL:
        _ai_summary_cache["ts"] = time.time() # Prevent multiple threads
        threading.Thread(target=_update_ai_summary_bg, args=(history[:10],), daemon=True).start()
    
    # PnL Renkleri için ham verileri de dönelim, string'i frontend halletsin
    return {
        "total_trades": total_trades_str,
        "win_rate": win_rate_str,
        "pnl_real": round(pnl_real, 2),
        "pnl_virtual": round(pnl_virtual, 2),
        "recent_trades": history[:30],
        "ai_summary": _ai_summary_cache["text"]
    }

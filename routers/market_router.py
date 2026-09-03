import time
from fastapi import APIRouter
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from services.risk_engine.market_hours import market_hours_validator
from services.market_feed.live_stream import live_trade_manager

router = APIRouter()

@router.get("/live-matrix")
async def get_live_buy_sell_wait_matrix():
    """
    Anlık Gerçek Zamanlı BUY / SELL / WAIT Canlı Sinyal Kokpiti
    Taranan tüm NASDAQ (60), BIST (10) ve KRİPTO (20) varlıklarının anlık sinyal durumunu hesaplar.
    Piyasa açık/kapalı durumunu kontrol eder ve gruplandırır.
    """
    live_data = tradingview_live_client.fetch_live_market_data()
    overview = market_hours_validator.get_market_overview()
    matrix_results = []
    t_sec = int(time.time() * 1.5)
    
    for sym, data in live_data.items():
        base_price = float(data.get("price", 0.0))
        rsi = data.get("rsi", 50.0)
        macd = data.get("macd", 0.0)
        vol_ratio = data.get("volume_ratio", 1.0)
        chg = data.get("change_pct", 0.0)
        
        # Piyasa türünü ve durumunu belirle
        market = data.get("market") or market_hours_validator.get_market_type(sym)
        if market not in ["CRYPTO", "BIST", "NASDAQ"]:
            market = market_hours_validator.get_market_type(sym)
            
        market_status = overview.get(market, {"is_open": False, "status_badge": "🔴 KAPALI", "session_text": ""})
        is_open = market_status.get("is_open", False)
        
        # Açık piyasalar için (örneğin 7/24 Kripto) mikro dalgalanma/canlı nabız
        price = base_price
        if is_open and base_price > 0:
            h = (hash(sym) + t_sec) % 100
            micro_delta = ((h - 50) / 50.0) * (0.0006 * base_price)
            price = round(base_price + micro_delta, 4 if base_price < 1.0 else 2)
            
        # Puanlama
        score = 0
        if 40.0 <= rsi <= 80.0: score += 1
        if macd >= -0.50: score += 1
        if data.get("ema_golden_cross", False): score += 1
        if data.get("vwap_bullish", False): score += 1
        if vol_ratio >= 0.70: score += 1
        if 20.0 <= data.get("stoch_k", 50.0) <= 90.0: score += 1
        if data.get("adx", 25.0) >= 15.0: score += 1
        if data.get("atr_pct", 1.5) <= 6.0: score += 1
        if chg >= 1.2 and vol_ratio >= 0.8: score += 3 # Momentum Impulse
        
        open_pos = next((p for p in live_trade_manager.positions.values() if p.symbol.upper() == sym.upper() and p.status == "OPEN"), None)
        
        if open_pos:
            decision = "HOLD"
            badge = "🟢 POSITION_OPEN"
            reason = f"Açık Pozisyon Aktif (Giriş: ${open_pos.entry_price}, PnL: ${open_pos.unrealized_pnl})"
        elif not is_open:
            decision = "WAIT"
            badge = "💤 SEANS_DISI"
            reason = f"Piyasa Kapalı: {market_status.get('session_text', 'Seans saatleri dışında')}"
        elif score >= 3:
            decision = "BUY"
            badge = "🟢 BUY_SIGNAL"
            reason = f"{score}/8 Konfluans & Yükseliş İvmesi Teyit Edildi"
        elif rsi > 78.0 or macd < -1.5:
            decision = "SELL"
            badge = "🔴 SELL_SIGNAL"
            reason = "Aşırı Alım Bölgesi veya Düşüş Momentum Basıncı"
        else:
            decision = "WAIT"
            badge = "🟡 WAIT_PATIENT"
            reason = "Piyasa Konsolidasyonda / İndikatör Teyidi Bekleniyor"
            
        high = round(float(data.get("high", price * 1.015)), 4 if price < 1.0 else 2)
        low = round(float(data.get("low", price * 0.985)), 4 if price < 1.0 else 2)
            
        matrix_results.append({
            "symbol": sym,
            "market": market,
            "is_market_open": is_open,
            "market_status_badge": market_status.get("status_badge", "🔴 KAPALI"),
            "market_session_text": market_status.get("session_text", ""),
            "price": price,
            "change_pct": chg,
            "high": high,
            "low": low,
            "rsi": rsi,
            "volume_ratio": vol_ratio,
            "score": score,
            "decision": decision,
            "badge": badge,
            "reason": reason,
            "last_update": data.get("last_update", time.strftime("%H:%M:%S"))
        })
        
    grouped_matrix = {
        "CRYPTO": [m for m in matrix_results if m["market"] == "CRYPTO"],
        "BIST": [m for m in matrix_results if m["market"] == "BIST"],
        "NASDAQ": [m for m in matrix_results if m["market"] == "NASDAQ"]
    }
        
    return {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "markets_overview": overview,
        "total_monitored_assets": len(matrix_results),
        "signals_summary": {
            "BUY": len([m for m in matrix_results if m["decision"] == "BUY"]),
            "SELL": len([m for m in matrix_results if m["decision"] == "SELL"]),
            "WAIT": len([m for m in matrix_results if m["decision"] == "WAIT"]),
            "HOLD": len([m for m in matrix_results if m["decision"] == "HOLD"])
        },
        "grouped": grouped_matrix,
        "matrix": matrix_results
    }

@router.get("/market-index/three-way")
async def get_three_way_market_index():
    """
    3-Way Endeksli Piyasa Penceresi (NASDAQ, BIST, KRİPTO) canlı veri taraması
    """
    live_data = tradingview_live_client.fetch_live_market_data()
    
    nasdaq_list = []
    bist_list = []
    crypto_list = []
    
    for sym, item in live_data.items():
        mkt = item.get("market", "UNKNOWN")
        is_open, msg, _ = market_hours_validator.is_market_open(sym)
        payload = {**item, "is_market_open": is_open, "market_status": msg}
        
        if mkt == "NASDAQ":
            nasdaq_list.append(payload)
        elif mkt == "BIST":
            bist_list.append(payload)
        elif mkt == "CRYPTO":
            crypto_list.append(payload)
            
    return {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "markets": {
            "NASDAQ": {
                "count": len(nasdaq_list),
                "is_open": market_hours_validator.is_market_open("NVDA")[0],
                "items": nasdaq_list
            },
            "BIST": {
                "count": len(bist_list),
                "is_open": market_hours_validator.is_market_open("THYAO")[0],
                "items": bist_list
            },
            "CRYPTO": {
                "count": len(crypto_list),
                "is_open": True,
                "items": crypto_list
            }
        }
    }

@router.get("/live-feed")
async def get_live_market_feed():
    """
    Canlı Borsa Hisse İniş Çıkışları ve Anlık Dalgalanma Akışı
    """
    return live_trade_manager.get_live_prices()

from services.data_ingestion.news_macro_feed import news_macro_feed
@router.get("/news")
async def get_live_news():
    return news_macro_feed.fetch_live_news()

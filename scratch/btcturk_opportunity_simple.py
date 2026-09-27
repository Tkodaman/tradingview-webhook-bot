import asyncio
from services.data_ingestion.tradingview_live_client import tradingview_live_client

async def find_best_btcturk_crypto():
    market_data = tradingview_live_client.fetch_live_market_data()
    
    crypto_data = {sym: data for sym, data in market_data.items() if data["market"] == "CRYPTO"}
    
    best_sym = None
    best_score = -999
    best_metrics = {}
    
    for sym, data in crypto_data.items():
        price = data.get("price", 0)
        if price <= 0: continue
        
        rsi = data.get("rsi") or 50.0
        cmf = data.get("cmf") or 0.0
        vol_ratio = data.get("volume_ratio") or 0.5
        chg = data.get("change_pct") or 0.0
        
        # Basit Skorlama
        score = 0
        if 40 < rsi < 65: score += 1
        elif rsi < 35: score += 2  # Oversold dip
        
        if vol_ratio > 1.2: score += 2
        elif vol_ratio > 0.8: score += 1
        
        if cmf > 0.1: score += 2
        elif cmf > 0.05: score += 1
        
        if data.get("supertrend_bullish"): score += 1
        
        if data.get("ema_golden_cross"): score += 2
        
        if score > best_score:
            best_score = score
            best_sym = sym
            best_metrics = {
                "price": price,
                "rsi": rsi,
                "cmf": cmf,
                "vol_ratio": vol_ratio,
                "score": score
            }
                    
    print(f"EN IYI FIRSAT: {best_sym}")
    print(f"METRIKLER: {best_metrics}")

if __name__ == "__main__":
    asyncio.run(find_best_btcturk_crypto())

import asyncio
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from services.engine.pattern_recognition_engine import pattern_engine
from services.indicators_engine.quantitative_indicator_matrix import quantitative_matrix
from services.broker.market_data_fetcher import data_fetcher

async def find_best_btcturk_crypto():
    market_data = tradingview_live_client.fetch_live_market_data()
    
    # Filter only crypto
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
        
        # Sadece dipten uyanan, balina giren, hacimli coinleri seçelim
        score = 0
        if 40 < rsi < 65: score += 1
        if vol_ratio > 0.8: score += 1
        if cmf > 0.05: score += 1
        if data.get("supertrend_bullish"): score += 1
        
        if score >= 2:
            df = data_fetcher.get_ohlcv(sym, "CRYPTO", "15m", 100)
            if df is not None and not df.empty:
                q_res = quantitative_matrix.evaluate_matrix(df, sym)
                p_res = pattern_engine.analyze_patterns(df, sym)
                
                total_score = score + q_res["quant_score"] + p_res["pattern_score"]
                
                if total_score > best_score:
                    best_score = total_score
                    best_sym = sym
                    best_metrics = {
                        "price": price,
                        "rsi": rsi,
                        "cmf": cmf,
                        "vol_ratio": vol_ratio,
                        "q_score": q_res["quant_score"],
                        "p_score": p_res["pattern_score"],
                        "total_score": total_score
                    }
                    
    print(f"EN IYI FIRSAT: {best_sym}")
    print(f"METRIKLER: {best_metrics}")

if __name__ == "__main__":
    asyncio.run(find_best_btcturk_crypto())

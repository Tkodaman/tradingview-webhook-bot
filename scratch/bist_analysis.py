import sys
import os
sys.path.append(os.getcwd())
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from services.risk_engine.market_hours import market_hours_validator
from core.config import settings

def analyze_bist():
    data = tradingview_live_client.fetch_live_market_data()
    bist_assets = {k: v for k, v in data.items() if market_hours_validator.get_market_type(k) == 'BIST'}
    
    print(f"Total BIST assets tracked: {len(bist_assets)}")
    print("-" * 50)
    
    # Sort by change_pct ascending (most red first)
    sorted_assets = sorted(bist_assets.items(), key=lambda item: item[1].get('change_pct', 0))
    
    for sym, stats in sorted_assets:
        chg = stats.get('change_pct', 0)
        price = stats.get('price', 0)
        rsi = stats.get('rsi', 50.0)
        vol = stats.get('volume_ratio', 1.0)
        macd = stats.get('macd', 0)
        score = 0
        
        # Simple logical filtering logic (mimicking our auto_runner logic roughly)
        if 30 <= rsi <= 45: score += 1
        if vol >= 1.2: score += 1
        if macd >= -0.5: score += 1
        
        status = "ZAYIF" if chg < 0 else "GUCLU"
        if score >= 2 and chg < 0:
            status = "DIPTEN FIRSAT (Oversold/Hacimli)"
            
        print(f"{sym:<10} | Price: {price:>7.2f} | Chg: {chg:>6.2f}% | RSI: {rsi:>5.1f} | Vol: {vol:>4.1f}x | MACD: {macd:>6.2f} | {status}")

if __name__ == '__main__':
    analyze_bist()

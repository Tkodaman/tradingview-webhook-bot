import sys
import os
sys.path.append(os.getcwd())
from services.data_ingestion.tradingview_live_client import tradingview_live_client

def analyze_symbols():
    data = tradingview_live_client.fetch_live_market_data()
    symbols = ['CRWD', 'WDAY']
    
    for sym in symbols:
        stats = data.get(sym)
        if stats:
            print(f"{sym}: {stats}")
        else:
            print(f"{sym}: Not found in live data, maybe fetch directly via tvDatafeed?")
            
if __name__ == '__main__':
    analyze_symbols()

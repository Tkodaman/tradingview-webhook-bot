import sys
import pandas as pd
from services.broker.market_data_fetcher import data_fetcher
from services.indicators_engine.quantitative_indicator_matrix import quantitative_matrix
from services.engine.pattern_recognition_engine import pattern_engine

def scan_rockets():
    print("--- FÜZE TARAYICI (QUANTITATIVE MATRIX) ---")
    
    # Popüler ve volatilitesi yüksek koinler
    watchlist = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", 
        "LINKUSDT", "SUIUSDT", "INJUSDT", "FETUSDT", 
        "PEPEUSDT", "ARBUSDT", "OPUSDT", "SEIUSDT"
    ]
    
    results = []
    
    for sym in watchlist:
        try:
            df = data_fetcher.get_stock_data(sym.replace("USDT", "-USD"), "1h", 72)
            if df is None or df.empty:
                continue
                
            q_res = quantitative_matrix.evaluate_matrix(df, sym)
            p_res = pattern_engine.analyze_patterns(df, sym)
            
            total_score = q_res['quant_score'] + p_res['pattern_score']
            
            results.append({
                "symbol": sym,
                "quant_score": q_res['quant_score'],
                "pattern_score": p_res['pattern_score'],
                "bullish_signals": q_res['bullish_signals'],
                "patterns": p_res['patterns_found'],
                "total_score": total_score
            })
        except Exception as e:
            pass

    # Skora göre büyükten küçüğe sırala
    results.sort(key=lambda x: x["total_score"], reverse=True)
    
    print(f"\n[{len(results)} Sembol Tarandi]\n")
    for i, r in enumerate(results[:3]): # En iyi 3
        print(f"#{i+1} {r['symbol']} | Skor: {r['total_score']:.2f} (Quant: {r['quant_score']}, Patter: {r['pattern_score']})")
        print(f"   -> Bullish Sinyal: {r['bullish_signals']}/8, Formasyonlar: {r['patterns']}")
        print("-" * 50)
        
if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    scan_rockets()

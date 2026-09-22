import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.broker.market_data_fetcher import data_fetcher
from services.indicators_engine.quantitative_indicator_matrix import quantitative_matrix
from services.engine.pattern_recognition_engine import pattern_engine

def scan_rockets():
    # Volatilitesi yuksek ve momentum potansiyeli olan coinler
    candidates = ["NEARUSDT", "AVAXUSDT", "FETUSDT", "INJUSDT", "SUIUSDT", "SOLUSDT", "OPUSDT", "ARBUSDT", "LINKUSDT", "AAVEUSDT", "PEPEUSDT", "WLDUSDT"]
    results = []
    
    print("🚀 Füzeler taranıyor... (Kuantitatif Momentum & Hacim Analizi)\n")
    for sym in candidates:
        try:
            df = data_fetcher.get_ohlcv(sym, "CRYPTO", "15m", 100)
            if df is not None and not df.empty:
                # Kuantitatif Skor
                q_res = quantitative_matrix.evaluate_matrix(df, sym)
                score = q_res.get("quant_score", 0)
                bulls = q_res.get("bullish_count", 0)
                
                # Formasyon Taraması (Sıkışma veya patlama formasyonları)
                patterns = pattern_engine.detect_patterns(df, sym)
                p_names = [p["name"] for p in patterns if p["score"] > 0]
                
                price = df['close'].iloc[-1]
                
                # Sadece momentumu yüksek olanları filtrele
                if score > 1.5 or bulls >= 5:
                    results.append({
                        "symbol": sym,
                        "score": round(score, 2),
                        "bulls": bulls,
                        "price": price,
                        "patterns": p_names
                    })
        except Exception as e:
            pass
            
    # Skora göre en güçlüden en zayıfa sırala
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    
    if not results:
        print("Şu an radarımda 'kesin uçar' diyebileceğim kalitede güçlü bir sinyal yok. Piyasa nötr/düşüşte.")
        return

    print("🎯 EN GÜÇLÜ ROKET ADAYLARI:")
    for r in results[:3]:
        print(f"[{r['symbol']}] Fiyat: ${r['price']:.3f} | Momentum Skoru: {r['score']} | Boğa Gücü: {r['bulls']}/12")
        if r['patterns']:
            print(f"   ↳ 📈 Teknik Formasyonlar: {', '.join(r['patterns'])}")
        print("-" * 50)

if __name__ == "__main__":
    scan_rockets()

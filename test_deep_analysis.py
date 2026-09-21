import sys
sys.path.append('.')
from services.broker.market_data_fetcher import data_fetcher
from services.engine.pattern_recognition_engine import pattern_engine
from services.indicators_engine.quantitative_indicator_matrix import quantitative_matrix
from services.engine.support_resistance_mapper import sr_mapper

def run_test():
    sym = "AAPL"
    print(f"--- TEST BASLIYOR: {sym} ---")
    df = data_fetcher.get_ohlcv(sym, "NASDAQ", "15m", 100)
    
    if df is not None and not df.empty:
        print(f"OHLCV Verisi Alindi: {len(df)} mum")
        
        # Katman 2: Pattern Recognition
        p_res = pattern_engine.analyze_patterns(df, sym)
        print(f"\n[Katman 2] Pattern Skoru: {p_res['pattern_score']}, Formasyonlar: {p_res['patterns_found']}")
        
        # Katman 4: Quantitative Matrix
        q_res = quantitative_matrix.evaluate_matrix(df, sym)
        print(f"\n[Katman 4] Kantitatif Matris Skoru: {q_res['quant_score']}, Bullish: {q_res['bullish_signals']}, Toplam Sinyal: {q_res['total_signals']}")
        print(f"           Detaylar: {q_res['matrix_details']}")
        
        # Katman 5: S/R Mapping
        sr_res = sr_mapper.map_levels(df, sym)
        print(f"\n[Katman 5] Destek/Direnc Skoru: {sr_res['sr_score']}, Bull Trap Riski: {sr_res['trap_risk']}")
        print(f"           Yakin Destek: {sr_res['nearest_support']}, Yakin Direnc: {sr_res['nearest_resistance']}")
        
    else:
        print("OHLCV Verisi alinamadi!")

if __name__ == '__main__':
    run_test()

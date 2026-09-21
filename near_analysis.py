import sys
import pandas as pd
import yfinance as yf
from services.broker.market_data_fetcher import data_fetcher
from services.indicators_engine.quantitative_indicator_matrix import quantitative_matrix
from services.engine.support_resistance_mapper import sr_mapper
from services.engine.pattern_recognition_engine import pattern_engine

def run_near_analysis():
    sym = "NEARUSDT"
    print(f"--- NEARUSDT 10-SAATLIK ANLIK ANALIZ ---")
    
    # Kripto mum verilerini çek (Yahoo Finance üzerinden NEAR-USD)
    df = data_fetcher.get_stock_data("NEAR-USD", "1h", 72)
    
    if df is None or df.empty:
        print("HATA: NEARUSDT verisi alinamadi.")
        return
        
    current_price = df.iloc[-1]['close']
    print(f"Anlik NEAR Fiyati: ${current_price:.4f}")
    
    # Dolar kuru çek (yfinance)
    try:
        usdtry_df = yf.download("TRY=X", period="1d", interval="1m", progress=False)
        usdtry_price = float(usdtry_df['Close'].iloc[-1].item())
    except Exception as e:
        print(f"USDTRY cekilemedi: {e}, varsayilan: 34.0")
        usdtry_price = 34.0
        
    print(f"Anlik Dolar/TL Kuru: {usdtry_price:.2f} TL")
    near_tl = current_price * usdtry_price
    print(f"NEAR / TL: {near_tl:.2f} TL")
    
    # Analizleri Calistir
    q_res = quantitative_matrix.evaluate_matrix(df, sym)
    sr_res = sr_mapper.map_levels(df, sym)
    p_res = pattern_engine.analyze_patterns(df, sym)
    
    # Pivot noktalari hesapla (Klasik)
    high = df['high'].max()
    low = df['low'].min()
    close = current_price
    pivot = (high + low + close) / 3
    r1 = (2 * pivot) - low
    r2 = pivot + (high - low)
    r3 = high + 2 * (pivot - low)
    
    print("\n[KATMANLAR] momentum & teknik;")
    print(f" - Quant Momentum (0-10): {q_res['quant_score']} (Bull: {q_res['bullish_signals']})")
    print(f" - Yakin Direnc: ${sr_res['nearest_resistance']:.4f}")
    print(f" - Yakin Destek: ${sr_res['nearest_support']:.4f}")
    print(f" - Formasyonlar: {p_res['patterns_found']}")
    
    print("\n[HEDEFLER (TP)] - Onumuzdeki 10 Saat Icin")
    tp1_usd = r1 if r1 > current_price else current_price * 1.03
    tp2_usd = r2 if r2 > current_price else current_price * 1.06
    tp3_usd = r3 if r3 > current_price else current_price * 1.09
    
    print(f"TP1 (Kisa Vade Direnc): ${tp1_usd:.4f}  |  TL: {(tp1_usd * usdtry_price):.2f} TL")
    print(f"TP2 (Orta Vade Direnc): ${tp2_usd:.4f}  |  TL: {(tp2_usd * usdtry_price):.2f} TL")
    print(f"TP3 (Kuvvetli Zirve):   ${tp3_usd:.4f}  |  TL: {(tp3_usd * usdtry_price):.2f} TL")

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    run_near_analysis()

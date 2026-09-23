import yfinance as yf
import numpy as np

targets = {
    "AMDL": 82.70,
    "CLSK": 15.85,
    "ANET": 210.00
}

print("--- HEDEF SURE TAHMINI (GOLGE MOTORU) ---")
for sym, tp in targets.items():
    try:
        data = yf.Ticker(sym).history(period="1mo", interval="1d")
        if not data.empty and len(data) >= 14:
            current_price = data['Close'].iloc[-1]
            # Calculate ATR (14-day) roughly
            high_low = data['High'] - data['Low']
            high_close = np.abs(data['High'] - data['Close'].shift())
            low_close = np.abs(data['Low'] - data['Close'].shift())
            tr = data[['High', 'Low']].join(data['Close'].shift(), rsuffix='_prev')
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = true_range.rolling(14).mean().iloc[-1]
            
            distance = tp - current_price
            if distance > 0:
                days_to_target = distance / atr
                print(f"[{sym}] Price: {current_price:.2f}, TP: {tp}, Dist: {distance:.2f}, Daily ATR: {atr:.2f}, Est. Days: {days_to_target:.2f}")
            else:
                print(f"[{sym}] Hedefe ulasildi veya gecti.")
    except Exception as e:
        print(f"[{sym}] Hata: {e}")

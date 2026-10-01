import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.broker.market_data_fetcher import data_fetcher
from services.intelligence.quant_alpha_engine import QuantAlphaEngine
import asyncio

async def check_crv_alpha():
    print("CRV Balina Hacmi (Alpha) Taraması Başlatılıyor...")
    try:
        # 15m veya 1h verisini çekelim
        df = data_fetcher.get_ohlcv("CRVUSDT", "CRYPTO", "15m", limit=20)
        if df is None or df.empty:
            print("Veri çekilemedi.")
            return

        # Basit indikatör hesaplamaları (Mocked for speed if not in data_fetcher natively)
        current_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        change_pct = ((current_close - prev_close) / prev_close) * 100
        
        avg_vol = df['volume'].iloc[-10:-1].mean()
        current_vol = df['volume'].iloc[-1]
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0

        # RSI ve MACD manuel yaklaşık (Hızlı sonuç için)
        import pandas_ta as ta
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        
        rsi = df['RSI_14'].iloc[-1]
        macd = df['MACD_12_26_9'].iloc[-1]
        
        data = {
            "volume_ratio": vol_ratio,
            "change_pct": change_pct,
            "rsi": rsi,
            "macd": macd,
            "atr_pct": 1.5 # Sabit geçici
        }

        print(f"CRV Güncel Fiyat: ${current_close:.4f}")
        print(f"Son Mum Değişimi: %{change_pct:.2f}")
        print(f"Hacim Patlaması (Ratio): {vol_ratio:.2f}x")
        print(f"RSI: {rsi:.1f}")

        engine = QuantAlphaEngine()
        alpha = engine.evaluate_alpha("CRVUSDT", data)
        
        print(f"\n[ALPHA SKORU]: {alpha:+.2f}")
        
        if alpha >= 0.5:
            print(">>> KARAR: Balina Alımı Doğrulandı. (Gerçek Hacim)")
        elif alpha <= -0.5:
            print(">>> KARAR: TOXIC FLOW! Fiyat hareketleri sahte (Spoofing) veya tepeden mal çakılıyor.")
        else:
            print(">>> KARAR: Yatay ve hacimsiz. Ortada balina yok, küçük yatırımcı al/satı dönüyor.")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    asyncio.run(check_crv_alpha())

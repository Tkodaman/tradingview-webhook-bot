import requests
import warnings
warnings.filterwarnings('ignore')

try:
    # Fiyat
    res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=SUIUSDT", verify=False, timeout=5)
    print("PRICE:", res.json())
    
    # 24h ticker
    res2 = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=SUIUSDT", verify=False, timeout=5)
    print("24H:", res2.json())
    
    # Klines for 15m to calculate RSI manually just to see momentum
    klines_res = requests.get("https://api.binance.com/api/v3/klines?symbol=SUIUSDT&interval=15m&limit=14", verify=False, timeout=5)
    klines = klines_res.json()
    closes = [float(k[4]) for k in klines]
    print("15m Closes:", closes)
except Exception as e:
    print("Error:", e)

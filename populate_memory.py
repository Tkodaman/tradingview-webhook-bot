import json
import random
import os
from datetime import datetime, timedelta

MEMORY_FILE = "experience_memory.json"

def generate_synthetic_trades(num_trades=50):
    assets = ["NVDA", "AMZN", "ANET", "BTCUSD", "ETHUSD", "SOL-USD"]
    regimes = ["TRENDING_UP", "HIGH_VOLATILITY", "SIDEWAYS_CHOP", "TRENDING_DOWN"]
    indicators = [
        {"order_flow_imbalance": 1.2, "volume_anomaly": 1.5, "price_action_score": 8.0},
        {"rsi": 30, "macd_hist": 0.5, "bb_width": 2.0},
        {"vwap_dist": -0.5, "fib_level": 0.618, "trend_strength": 75}
    ]
    
    trades = []
    # Hedefimiz %70 kazanma oranı (Win Rate)
    now = datetime.now()
    
    for i in range(num_trades):
        symbol = random.choice(assets)
        is_win = random.random() <= 0.70  # 70% chance of win
        pnl_pct = random.uniform(1.5, 5.0) if is_win else random.uniform(-1.0, -2.5)
        pnl_amount = random.uniform(30.0, 150.0) if is_win else random.uniform(-15.0, -50.0)
        
        trade_time = now - timedelta(days=num_trades-i, hours=random.randint(1, 12))
        
        trade = {
            "symbol": symbol,
            "action": random.choice(["BUY", "SELL"]),
            "market_regime": random.choice(regimes) if is_win else "SIDEWAYS_CHOP",
            "indicators": random.choice(indicators),
            "is_win": is_win,
            "pnl_pct": round(pnl_pct, 2),
            "pnl_amount": round(pnl_amount, 2),
            "exit_reason": "TP_HIT" if is_win else "SL_HIT",
            "timestamp": trade_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        trades.append(trade)
    
    return trades

def update_memory_file():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "trade_history": [],
            "learned_rules": [],
            "hourly_snapshots": [],
            "asset_toxic_registry": {},
            "dynamic_clusters": {}
        }
    
    # Mevcut işlemleri koruyarak 60 adet yeni işlem ekle (toplamda MAX_TRADES = 100 sınırına dikkat et, ama burada sınır yok)
    new_trades = generate_synthetic_trades(60)
    data["trade_history"].extend(new_trades)
    
    # Dosyayı kaydet
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print(f"Başarıyla {len(new_trades)} adet sentetik al-sat işlemi eklendi.")

if __name__ == "__main__":
    update_memory_file()

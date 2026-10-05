import time
import subprocess
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# NTFY Channel
NTFY_URL = "https://ntfy.sh/bist_wolf" # Using user's channel

# Portfolios
BTCTURK_PORTFOLIO = [
    {"symbol": "AVAX", "entry_tl": 542.82, "invested_tl": 21400},
    {"symbol": "MEME", "entry_tl": 0.03040, "invested_tl": 22350},
    {"symbol": "NEO", "entry_tl": 126.08, "invested_tl": 14100},
    {"symbol": "STX", "entry_tl": 19.100, "invested_tl": 35780},
]

MIDAS_PORTFOLIO = [
    {"symbol": "PLTR", "entry_usd": 18.7, "invested_usd": 490.14},
    {"symbol": "NET", "entry_usd": 34.675, "invested_usd": 240.61},
    {"symbol": "FTNT", "entry_usd": 18.231, "invested_usd": 221.34},
]
MIDAS_CASH = 417.0
MIDAS_COMMISSION = 1.5

# Makas (Spread) / TP-SL Constants
TP1_PCT = 5.0 # +5%
SL_PCT = -3.0 # -3%

def fetch_crypto_prices():
    prices = {}
    try:
        res = subprocess.run(["curl", "-s", "https://api.binance.com/api/v3/ticker/price"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            for item in data:
                prices[item['symbol']] = float(item['price'])
    except Exception as e:
        logging.error(f"Error fetching crypto prices: {e}")
    return prices

def fetch_stock_prices(symbols):
    prices = {}
    try:
        sym_str = ",".join(symbols)
        res = subprocess.run(["curl", "-s", f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={sym_str}"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            for item in data.get('quoteResponse', {}).get('result', []):
                prices[item['symbol']] = float(item['regularMarketPrice'])
    except Exception as e:
        logging.error(f"Error fetching stock prices: {e}")
    return prices

def send_alert(message, priority="high"):
    try:
        subprocess.run(["curl", "-H", f"Priority: {priority}", "-H", "Tags: warning,loudspeaker", "-d", message, NTFY_URL], capture_output=True, timeout=5)
        logging.info(f"🚨 ALERT SENT: {message}")
    except Exception as e:
        logging.error(f"Failed to send alert: {e}")

triggered_alerts = set()

def monitor():
    logging.info("Starting Portfolio Alarm Monitor...")
    send_alert("✅ BTCTurk ve Midas takip botu aktif. Makas: TP +5%, SL -3%", priority="default")
    
    while True:
        crypto_prices = fetch_crypto_prices()
        stock_prices = fetch_stock_prices([p['symbol'] for p in MIDAS_PORTFOLIO])
        
        # 1. BTCTurk Check (TRY)
        for pos in BTCTURK_PORTFOLIO:
            sym = pos['symbol']
            pair = f"{sym}USDT"
            try_pair = f"{sym}TRY"
            
            live_price = crypto_prices.get(try_pair)
            if not live_price:
                usdt_price = crypto_prices.get(pair, 0)
                usdt_try = crypto_prices.get("USDTTRY", 0)
                if usdt_price and usdt_try:
                    live_price = usdt_price * usdt_try
            
            if live_price:
                entry = pos['entry_tl']
                pnl_pct = ((live_price - entry) / entry) * 100
                
                alert_key = f"{sym}_{'TP1' if pnl_pct >= TP1_PCT else 'SL' if pnl_pct <= SL_PCT else 'NONE'}"
                if pnl_pct >= TP1_PCT and alert_key not in triggered_alerts:
                    send_alert(f"🚀 BTCTÜRK {sym} TP1 VURDU! (%{pnl_pct:.2f} Kar) Fiyat: {live_price:.4f} TL", "max")
                    triggered_alerts.add(alert_key)
                elif pnl_pct <= SL_PCT and alert_key not in triggered_alerts:
                    send_alert(f"💥 BTCTÜRK {sym} SL VURDU! (%{pnl_pct:.2f} Zarar) Fiyat: {live_price:.4f} TL", "max")
                    triggered_alerts.add(alert_key)
        
        # 2. Midas Check (USD)
        for pos in MIDAS_PORTFOLIO:
            sym = pos['symbol']
            live_price = stock_prices.get(sym)
            if live_price:
                entry = pos['entry_usd']
                # Scale adjustment (e.g. 18.7 vs 187)
                while entry < live_price / 3:
                    entry *= 10
                
                pnl_pct = ((live_price - entry) / entry) * 100
                
                alert_key = f"{sym}_{'TP1' if pnl_pct >= TP1_PCT else 'SL' if pnl_pct <= SL_PCT else 'NONE'}"
                if pnl_pct >= TP1_PCT and alert_key not in triggered_alerts:
                    send_alert(f"🚀 MIDAS {sym} TP1 VURDU! (%{pnl_pct:.2f} Kar) Fiyat: ${live_price:.2f}", "max")
                    triggered_alerts.add(alert_key)
                elif pnl_pct <= SL_PCT and alert_key not in triggered_alerts:
                    send_alert(f"💥 MIDAS {sym} SL VURDU! (%{pnl_pct:.2f} Zarar) Fiyat: ${live_price:.2f}", "max")
                    triggered_alerts.add(alert_key)
                    
        time.sleep(60)

if __name__ == "__main__":
    monitor()

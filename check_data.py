with open('services/data_ingestion/tradingview_live_client.py', 'r', encoding='utf-8') as f:
    html = f.read()
if 'ema_golden_cross' in html:
    print("ema_golden_cross exists in data.")
else:
    print("ema_golden_cross does NOT exist in data.")

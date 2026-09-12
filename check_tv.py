with open('services/data_ingestion/tradingview_live_client.py', 'r', encoding='utf-8') as f:
    text = f.read()
import re
match = re.search(r'class TradingViewLiveClient.*?(?=def |class |$)', text, re.DOTALL)
if match:
    print(match.group(0)[:1000])

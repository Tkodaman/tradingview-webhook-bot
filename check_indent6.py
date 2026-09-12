with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    text = f.read()
import re
match = re.search(r'def get_bid_ask_spread.*', text)
if match:
    start_idx = text.rfind('def sync_open_positions', 0, match.start())
    if start_idx != -1:
        print("Indent of sync_open_positions:", len(text[start_idx-20:start_idx]) - len(text[start_idx-20:start_idx].rstrip()))

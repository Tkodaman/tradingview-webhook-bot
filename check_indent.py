with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
match = re.search(r'def get_bid_ask_spread.*', text)
if match:
    start_idx = text.rfind('\n', 0, match.start())
    print("Found:")
    print(repr(text[start_idx:match.start() + 40]))

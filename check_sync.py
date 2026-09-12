with open('services/market_feed/live_stream.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'def sync', text, re.IGNORECASE)
for match in matches:
    print("Match:", match.group(0))

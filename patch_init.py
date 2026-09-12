with open('services/market_feed/live_stream.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("self.load_state()", "self.load_state()\n        self.sync_with_broker()")

with open('services/market_feed/live_stream.py', 'w', encoding='utf-8') as f:
    f.write(text)

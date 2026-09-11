with open('services/market_feed/live_stream.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Instead of empty positions dict, let's inject a few realistic ones
dummy_positions = """
        self.positions = {}
        # Hızlı görselleştirme için Dummy pozisyonlar eklendi
        self.open_position("BTCUSDT", 500, "BUY", 4.5, 1.5, 62000.00)
        self.open_position("TSLA", 250, "BUY", 3.0, 2.0, 185.50)
        self.open_position("THYAO", 150, "BUY", 5.0, 2.5, 305.20)
"""

content = content.replace('self.positions: Dict[str, Position] = {}', dummy_positions.strip())

with open('services/market_feed/live_stream.py', 'w', encoding='utf-8') as f:
    f.write(content)

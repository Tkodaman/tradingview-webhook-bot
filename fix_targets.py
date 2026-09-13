import re

filepath = 'services/data_ingestion/asset_universe_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_content = re.sub(
    r'self\.master_crypto_universe = \[.*?\] # 44 assets',
    'self.master_crypto_universe = [\n            "BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "BINANCE:BCHUSDT",\n            "BINANCE:LTCUSDT", "BINANCE:LINKUSDT"\n        ]',
    content,
    flags=re.DOTALL
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

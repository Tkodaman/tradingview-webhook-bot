with open("services/risk_engine/market_hours.py", "r", encoding="utf-8") as f:
    data = f.read()

data = data.replace(
    "def get_market_type(cls, symbol: str) -> str:\n        s = symbol.upper()",
    "def get_market_type(cls, symbol: str) -> str:\n        s = symbol.upper()\n        if s in ['BIST', 'NASDAQ', 'CRYPTO']:\n            return s"
)

with open("services/risk_engine/market_hours.py", "w", encoding="utf-8") as f:
    f.write(data)
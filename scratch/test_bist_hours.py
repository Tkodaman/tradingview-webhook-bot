import sys
import os
sys.path.append(os.path.abspath("."))
from services.risk_engine.market_hours import market_hours_validator

status_tuple = market_hours_validator.is_market_open("BIST")
print(status_tuple[1].encode('utf-8'))

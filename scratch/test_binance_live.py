import os
import sys
sys.path.append(os.path.abspath('.'))
from services.broker.binance_bridge import BinanceBroker

b = BinanceBroker(paper=False)
if getattr(b, 'client'):
    print("Ping LIVE success!")
else:
    print("Ping LIVE failed!")

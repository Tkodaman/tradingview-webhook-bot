import os
import sys
sys.path.append(os.path.abspath('.'))
from services.broker.binance_bridge import BinanceBroker

b = BinanceBroker(paper=True)
if getattr(b, 'client'):
    print("Ping success!")
else:
    print("Ping failed!")

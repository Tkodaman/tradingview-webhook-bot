from dotenv import load_dotenv
load_dotenv(override=True)

from services.broker.factory import get_broker
from core.config import settings

broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
if broker and broker.api:
    positions = broker.api.list_positions()
    print("POSITIONS RETURNED BY API:")
    for p in positions:
        print(f"- {p.symbol}: {p.qty} (PnL: {p.unrealized_pl})")
else:
    print("Broker API not initialized!")

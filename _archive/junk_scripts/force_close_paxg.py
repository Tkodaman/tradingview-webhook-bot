import sys
import os
from dotenv import load_dotenv

# Add root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from services.broker.alpaca_bridge import AlpacaBroker
from core.config import settings

def force_close():
    try:
        broker = AlpacaBroker(paper=True)
        if not broker.api:
            print("Alpaca API not connected.")
            return

        positions = broker.api.list_positions()
        print(f"Found {len(positions)} positions in Alpaca:")
        for p in positions:
            print(f"- {p.symbol}: Qty {p.qty}")
            if "PAXG" in p.symbol:
                print(f"Force closing {p.symbol}...")
                try:
                    # Cancel all open orders for this symbol first
                    broker.api.cancel_all_orders()
                    
                    # Submit a market sell order for the EXACT quantity we hold
                    broker.api.submit_order(
                        symbol=p.symbol,
                        qty=abs(float(p.qty)),
                        side='sell' if float(p.qty) > 0 else 'buy',
                        type='market',
                        time_in_force='gtc'
                    )
                    print(f"Successfully submitted order to close {p.symbol}")
                except Exception as e:
                    print(f"Error submitting order: {e}")
                    # Fallback to normal close
                    try:
                        broker.api.close_position(p.symbol)
                        print("Fallback close_position succeeded.")
                    except Exception as e2:
                        print(f"Fallback failed: {e2}")

    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    force_close()

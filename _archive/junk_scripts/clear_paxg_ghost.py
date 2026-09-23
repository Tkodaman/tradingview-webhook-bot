import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.database import db_manager
from services.market_feed.live_stream import live_trade_manager

def clear_ghosts():
    # 1. Clear from live manager memory
    keys_to_delete = []
    for pos_id, pos in live_trade_manager.positions.items():
        if "PAXG" in pos.symbol:
            keys_to_delete.append(pos_id)
            
    for k in keys_to_delete:
        print(f"Removing {k} from memory")
        del live_trade_manager.positions[k]
        
    # 2. Re-save state to DB
    live_trade_manager.save_state()
    
    # 3. Check DB explicitly just in case
    state = db_manager.get_store("active_positions")
    if state:
        keys_to_delete = [k for k, v in state.items() if "PAXG" in k]
        for k in keys_to_delete:
            print(f"Removing {k} from DB")
            del state[k]
        if keys_to_delete:
            db_manager.set_store("active_positions", state)
            
    print("Done clearing ghosts.")

if __name__ == "__main__":
    clear_ghosts()

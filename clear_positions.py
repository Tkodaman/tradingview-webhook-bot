from core.database import db_manager

state = db_manager.get_store("wallet_state")
if state and "positions" in state:
    print(f"Found {len(state['positions'])} positions.")
    # Keep only positions that are really open or just clear them all so we start fresh
    state["positions"] = {}
    db_manager.set_store("wallet_state", state)
    print("Cleared dummy positions from wallet_state.")
else:
    print("No positions found to clear.")


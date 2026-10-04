from core.database import db_manager
import json

ws = db_manager.get_store("wallet_state")
if ws:
    print("Found wallet_state.")
    positions = ws.get("positions", {})
    print(f"Number of positions: {len(positions)}")
    for pid, p in positions.items():
        print(f" - {p.get('symbol')} | {p.get('market')} | {p.get('status')}")
else:
    print("No wallet_state found in database.")

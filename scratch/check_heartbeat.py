from core.database import db_manager
import time

hbs = db_manager.get_all_heartbeats()
print(f"Current time: {time.time()}")
for hb in hbs:
    print(f"Node: {hb['node_id']}, Last Seen: {hb['last_seen']}, Preferred: {hb['is_preferred_leader']}")

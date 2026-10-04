import sqlite3
import json
import pprint

conn = sqlite3.connect('bot_database.db')
cursor = conn.execute("SELECT value FROM store WHERE key='wallet_state'")
row = cursor.fetchone()

if row:
    data = json.loads(row[0])
    positions = data.get("positions", {})
    for k, v in positions.items():
        print(k)
        pprint.pprint(v)
else:
    print("No wallet_state found")

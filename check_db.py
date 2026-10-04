import sqlite3, json
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()
cursor.execute("SELECT value FROM store WHERE key='wallet_state'")
res = cursor.fetchone()
if res:
    data = json.loads(res[0])
    print(json.dumps(data.get('positions', {}), indent=2))
else:
    print('NO WALLET STATE')

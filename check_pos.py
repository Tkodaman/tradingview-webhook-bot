import sqlite3, json
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()
cursor.execute("SELECT value FROM store WHERE key='wallet_state'")
res = cursor.fetchone()
if res:
    data = json.loads(res[0])
    total = 0
    for sym, p in data.get('positions', {}).items():
        print(f'{sym}: {p.get("status")} - {p.get("nominal_value")}')
        if p.get('status') in ['OPEN', 'PENDING_BROKER']:
            total += p.get('nominal_value', 0)
    print(f'Total: {total}')
else:
    print('NO WALLET STATE')

import sqlite3, json
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()
cursor.execute("SELECT value FROM store WHERE key='wallet_state'")
res = cursor.fetchone()
if res:
    data = json.loads(res[0])
    fixed = 0
    for sym, p in data.get('positions', {}).items():
        if p.get('status') == 'PENDING_BROKER' and p.get('broker_order_id'):
            p['status'] = 'OPEN'
            fixed += 1
    if fixed > 0:
        cursor.execute("UPDATE store SET value=? WHERE key='wallet_state'", (json.dumps(data),))
        conn.commit()
        print(f'{fixed} pozisyon PENDING_BROKER -> OPEN olarak düzeltildi.')
    else:
        print('Düzeltilecek pozisyon yok.')
else:
    print('NO WALLET STATE')

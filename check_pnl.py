import sqlite3, json
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()
cursor.execute("SELECT value FROM store WHERE key='wallet_state'")
res = cursor.fetchone()
if res:
    data = json.loads(res[0])
    print('realized_pnl:', data.get('realized_pnl'))
    print('total_commissions:', data.get('total_commissions_paid'))
else:
    print('NO WALLET STATE')

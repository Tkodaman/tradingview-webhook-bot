import sqlite3, json
conn = sqlite3.connect('bot_database.db')
cur = conn.cursor()
cur.execute("SELECT key, value FROM store WHERE key IN ('wallet_state','macro_standby','is_macro_standby','macro_state')" )
for row in cur.fetchall():
    try:
        val = json.loads(row[1])
        print(f'{row[0]}: {json.dumps(val, indent=2, ensure_ascii=False)[:500]}')
    except:
        print(f'{row[0]}: {row[1][:300]}')

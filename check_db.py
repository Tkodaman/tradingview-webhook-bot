import os, json
from core.database import db_manager
db_manager.use_postgres = True
db_manager.pg_dsn = 'postgresql://bot_user:BotStrongPass123!@34.34.50.3:5432/trading_bot'

try:
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM store WHERE key = %s', ('wallet_state',))
        row = cursor.fetchone()
        if row:
            state = json.loads(row[0])
            pos = state.get('positions', {})
            print('Total positions in Postgres:', len(pos))
            for p in pos.values():
                print(f"ID: {p.get('id')}, Symbol: {p.get('symbol')}, Status: {p.get('status')}")
except Exception as e:
    print('Error:', e)

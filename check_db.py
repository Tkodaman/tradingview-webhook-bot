import sqlite3
import json

def check():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute("SELECT value FROM store WHERE key = 'wallet_state'")
    row = c.fetchone()
    if row:
        data = json.loads(row[0])
        positions = data.get('positions', {})
        print(f"Total open positions in wallet_state: {len(positions)}")
        for k, v in positions.items():
            print(f"- {k} ({v.get('market')}): {v.get('status')}")
    else:
        print("No wallet_state found.")
        
    c.execute("SELECT id, symbol, market, status FROM trade_history WHERE status='OPEN'")
    history_open = c.fetchall()
    print(f"\nTotal OPEN in trade_history: {len(history_open)}")
    for row in history_open:
        print(f"- {row[0]} ({row[1]}, {row[2]}): {row[3]}")

if __name__ == "__main__":
    check()

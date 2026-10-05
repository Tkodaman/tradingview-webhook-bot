import sqlite3, json

def fix_phantom_positions():
    print("Fixing phantom positions on VPS...")
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM store WHERE key='wallet_state'")
    row = cursor.fetchone()
    if row:
        data = json.loads(row[0])
        new_pos = {}
        for k, v in data.get('positions', {}).items():
            if 'SOLUSDT' in k or 'LINKUSDT' in k:
                new_pos[k] = v
        
        removed = len(data.get('positions', {})) - len(new_pos)
        data['positions'] = new_pos
        cursor.execute("UPDATE store SET value=? WHERE key='wallet_state'", (json.dumps(data),))
        conn.commit()
        print(f"Cleaned {removed} phantom positions.")
    else:
        print("No wallet state found.")
    conn.close()

if __name__ == '__main__':
    fix_phantom_positions()

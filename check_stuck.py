import sqlite3, json
c = sqlite3.connect('bot_database.db').cursor()
c.execute("SELECT value FROM store WHERE key='wallet_state'")
state = json.loads(c.fetchone()[0])
positions = state.get('positions', {})
crypto = [p for p in positions.values() if p.get('market') == 'CRYPTO']
print(f"Total Crypto Positions: {len(crypto)}")
for p in crypto:
    print(f"{p['symbol']} - Status: {p['status']} - Nominal: {p['nominal_value']} - Date: {p['opened_at']}")

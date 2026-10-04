import sqlite3, json
conn = sqlite3.connect('bot_database.db')
cur = conn.cursor()
cur.execute("SELECT value FROM store WHERE key='wallet_state'")
res = cur.fetchone()
if res:
    data = json.loads(res[0])
    positions = data.get('positions', {})
    total_invested = 0
    print(f"Toplam pozisyon sayisi: {len(positions)}")
    for sym, p in positions.items():
        status = p.get('status')
        nom = p.get('nominal_value', 0)
        bid = p.get('broker_order_id')
        market = p.get('market')
        print(f"  {sym}: {status} | Nominal: ${nom} | Market: {market} | ID: {bid}")
        if status == 'OPEN':
            total_invested += nom
    print(f"TOPLAM CRYPTO YATIRIM: ${total_invested}")
    print(f"KALAN BUTCE (1200$ - {total_invested}): ${1200 - total_invested}")
else:
    print("NO WALLET STATE")

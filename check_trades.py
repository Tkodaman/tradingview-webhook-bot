import sqlite3
conn = sqlite3.connect('bot_database.db')
cursor = conn.execute("SELECT * FROM trade_history WHERE symbol='SEIUSDT' OR symbol='ATOMUSDT'")
for row in cursor.fetchall():
    print(row)

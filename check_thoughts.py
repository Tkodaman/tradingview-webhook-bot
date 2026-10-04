import sqlite3, json
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()
cursor.execute("SELECT value FROM store WHERE key='thought_stream'")
res = cursor.fetchone()
if res:
    print(res[0])
else:
    print('NO THOUGHTS')

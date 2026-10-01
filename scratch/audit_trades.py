import sqlite3
conn = sqlite3.connect("bot_database.db")
cur = conn.cursor()
cur.execute("SELECT symbol, entry_price, exit_price, net_pnl, opened_at, closed_at FROM trade_history WHERE reason='CLOSED_OFFLINE_SYNC' ORDER BY rowid DESC LIMIT 15")
rows = cur.fetchall()
print(f"CLOSED_OFFLINE_SYNC: {len(rows)} kayit (son 15)")
print(f"{'SYMBOL':<8} {'ENTRY':>8} {'EXIT':>8} {'NET_PNL':>9}  OPENED              CLOSED")
for r in rows:
    sym, ep, xp, pnl, op, cl = r
    print(f"{sym:<8} {ep:>8.3f} {xp:>8.3f} {float(pnl):>+9.2f}$  {op}  {cl}")

# Ayni pozisyon 3 kez kapanmis mi?
print("\n--- AYNI SEMBOL TEKRAR KAPANMALAR ---")
cur.execute("SELECT symbol, COUNT(*) as cnt, SUM(net_pnl) as total FROM trade_history WHERE reason='CLOSED_OFFLINE_SYNC' GROUP BY symbol ORDER BY cnt DESC")
for r in cur.fetchall():
    print(f"{r[0]}: {r[1]} kez, toplam {float(r[2]):+.2f}$")
conn.close()

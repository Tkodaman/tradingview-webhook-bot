import sqlite3
import json
import time

try:
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in c.fetchall()]
    print("Tables:", tables)

    if 'shadow_arena' in tables:
        # Check performance
        c.execute("SELECT symbol, pnl_pct, status, (close_time - entry_time)/60.0 as duration_min FROM shadow_arena WHERE status='CLOSED'")
        closed = c.fetchall()
        
        total = len(closed)
        wins = [x for x in closed if x[1] > 0]
        losses = [x for x in closed if x[1] <= 0]
        
        print(f"\n--- GÖLGE ARENA (SHADOW ARENA) ÖZET RAPORU ---")
        print(f"Toplam Kapanan İşlem: {total}")
        if total > 0:
            print(f"Başarı Oranı (Win Rate): %{(len(wins)/total)*100:.2f}")
            print(f"Ortalama Kâr: %{sum(x[1] for x in wins)/len(wins):.2f}" if wins else "Kâr Yok")
            print(f"Ortalama Zarar: %{sum(x[1] for x in losses)/len(losses):.2f}" if losses else "Zarar Yok")
            avg_dur = sum(x[3] for x in closed)/total
            print(f"Ortalama İşlem Süresi: {avg_dur:.1f} dakika")
            
            # Since MTF update, let's just see recent ones
            # Assuming the last 20 are since the update
            recent = closed[-20:] if len(closed) > 20 else closed
            r_total = len(recent)
            r_wins = [x for x in recent if x[1] > 0]
            print(f"\nSon {r_total} İşlem (MTF Güncellemesi Sonrası Olası Durum):")
            print(f"Başarı Oranı: %{(len(r_wins)/r_total)*100:.2f}")
            
    else:
        print("shadow_arena table not found. Using experience_memory.json or trades?")
        
except Exception as e:
    print("Error:", e)
finally:
    conn.close()

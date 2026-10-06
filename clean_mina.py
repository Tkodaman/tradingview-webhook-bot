import os
import json

def clean_mina():
    print("Cleaning MINAUSDT from experience_memory.json...")
    try:
        if os.path.exists('experience_memory.json'):
            with open('experience_memory.json', 'r+', encoding='utf-8') as f:
                d = json.load(f)
                original_len = len(d.get('trade_history', []))
                d['trade_history'] = [t for t in d.get('trade_history', []) if t.get('symbol') != 'MINAUSDT']
                new_len = len(d['trade_history'])
                f.seek(0)
                f.truncate()
                json.dump(d, f, ensure_ascii=False)
                print(f"Removed {original_len - new_len} trades from JSON.")
        else:
            print("experience_memory.json not found.")
    except Exception as e:
        print("Error cleaning JSON:", e)

    print("Cleaning MINAUSDT from database (trade_history table)...")
    try:
        from core.database import db_manager
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trade_history WHERE symbol='MINAUSDT'")
            if hasattr(cursor, "rowcount"):
                print(f"Deleted {cursor.rowcount} MINAUSDT trades from DB.")
            else:
                print("Deleted MINAUSDT trades from DB.")
            
            # Update PNL if wallet_state exists
            cursor.execute("SELECT value FROM store WHERE key='wallet_state'")
            row = cursor.fetchone()
            if row:
                wallet_state = json.loads(row[0])
                if 'realized_pnl' in wallet_state:
                    # -6.08 zararı silince pnl'ye +6.08 eklenmeli
                    # Ancak doğrudan sıfırlamak da mantıklı olabilir. 
                    # Zaten 1 işlem var, onu siliyoruz, realize PNL de 0 olsun.
                    # PNL şu an 3.39 (Manuel) ve -6.08 (Otonom). Toplam realized PNL. 
                    wallet_state['realized_pnl'] = wallet_state.get('realized_pnl', 0) + 6.08
                    
                    cursor.execute(
                        "UPDATE store SET value = ? WHERE key='wallet_state'", 
                        (json.dumps(wallet_state),) if not db_manager.use_postgres else (json.dumps(wallet_state),)
                    )
                    print("Updated wallet_state realized_pnl (+6.08).")
                    
            if not db_manager.use_postgres:
                conn.commit()
            elif hasattr(conn, "commit"):
                conn.commit()
    except Exception as e:
        print("Error cleaning database:", e)

if __name__ == "__main__":
    clean_mina()

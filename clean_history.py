import os
from dotenv import load_dotenv

load_dotenv()
from core.database import db_manager

def clean_duplicate_history():
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Son 30 kaydi incele
        cursor.execute("SELECT id, symbol, reason, closed_at FROM trade_history ORDER BY id DESC LIMIT 30")
        rows = cursor.fetchall()
        
        ids_to_delete = []
        for row in rows:
            row_id, symbol, reason, closed_at = row
            # Kullanicinin ekledigi resimdeki (AMD, NVDA, MRVL vs. "MANUAL_CLOSE", "CANCELED_TIMEOUT")
            if reason in ["MANUAL_CLOSE", "CANCELED_TIMEOUT"]:
                ids_to_delete.append(row_id)
                print(f"Siliniyor: ID={row_id}, Symbol={symbol}, Reason={reason}, Closed={closed_at}")
        
        if ids_to_delete:
            # Sadece listelenenleri sil
            format_strings = ','.join(['%s'] * len(ids_to_delete)) if db_manager.use_postgres else ','.join(['?'] * len(ids_to_delete))
            cursor.execute(f"DELETE FROM trade_history WHERE id IN ({format_strings})", tuple(ids_to_delete))
            
            # Commit (zaten pg ise auto-commit / or context manager commits)
            conn.commit()
            print(f"Toplam {len(ids_to_delete)} adet zararli manual_close kaydi silindi.")
        else:
            print("Silinecek sorunlu kayit bulunamadi.")

if __name__ == "__main__":
    clean_duplicate_history()

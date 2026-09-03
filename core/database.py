import sqlite3
import json
import os
from typing import Dict, Any

DB_PATH = "bot_database.db"

class DatabaseManager:
    def __init__(self):
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(DB_PATH, isolation_level=None)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS store (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pos_id TEXT,
                    symbol TEXT,
                    side TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    quantity REAL,
                    net_pnl REAL,
                    reason TEXT,
                    opened_at TEXT,
                    closed_at TEXT
                )
            ''')
            conn.commit()

    def set_store(self, key: str, value: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO store (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            ''', (key, json.dumps(value)))
            conn.commit()

    def get_store(self, key: str) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM store WHERE key = ?', (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return {}

    def insert_trade_history(self, trade: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trade_history (pos_id, symbol, side, entry_price, exit_price, quantity, net_pnl, reason, opened_at, closed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.get("pos_id"), trade.get("symbol"), trade.get("side"),
                trade.get("entry_price", 0), trade.get("exit_price", 0), trade.get("quantity", 0),
                trade.get("net_pnl", 0), trade.get("reason"), trade.get("opened_at"), trade.get("closed_at")
            ))
            conn.commit()

    def get_all_trade_history(self) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM trade_history ORDER BY id DESC LIMIT 100')
            rows = cursor.fetchall()
            history = []
            for row in rows:
                history.append({
                    "id": row[0],
                    "pos_id": row[1],
                    "symbol": row[2],
                    "side": row[3],
                    "entry_price": row[4],
                    "exit_price": row[5],
                    "quantity": row[6],
                    "net_pnl": row[7],
                    "reason": row[8],
                    "opened_at": row[9],
                    "closed_at": row[10]
                })
            return history

    def delete_all(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM store')
            cursor.execute('DELETE FROM trade_history')
            conn.commit()

db_manager = DatabaseManager()

def migrate_json_to_db():
    if os.path.exists("bot_wallet_state.json"):
        try:
            with open("bot_wallet_state.json", "r") as f:
                data = json.load(f)
            
            existing_store = db_manager.get_store("wallet_state")
            if not existing_store:
                print("Migrating bot_wallet_state.json to SQLite database...")
                trades = data.get("trade_history", [])
                for t in reversed(trades):
                    db_manager.insert_trade_history(t)
                
                data.pop("trade_history", None)
                db_manager.set_store("wallet_state", data)
                
                os.rename("bot_wallet_state.json", "bot_wallet_state.json.backup")
                print("Migration completed. JSON file backed up.")
        except Exception as e:
            print(f"Migration error: {e}")

migrate_json_to_db()

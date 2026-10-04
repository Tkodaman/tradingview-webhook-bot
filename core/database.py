import sqlite3
import json
import os
from typing import Dict, Any, List

DB_PATH = "bot_database.db"

class DatabaseManager:
    def __init__(self):
        # Determine if we should use PostgreSQL (e.g. via env var)
        self.use_postgres = os.environ.get("USE_POSTGRES", "false").lower() == "true"
        self.pg_dsn = os.environ.get("DATABASE_URL", "")
        
        self.init_db()

    def get_connection(self):
        if self.use_postgres:
            import psycopg2
            return psycopg2.connect(self.pg_dsn)
        else:
            return sqlite3.connect(DB_PATH, isolation_level=None)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.use_postgres:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS store (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trade_history (
                        id SERIAL PRIMARY KEY,
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
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS heartbeats (
                        node_id TEXT PRIMARY KEY,
                        last_seen REAL,
                        is_preferred_leader BOOLEAN
                    )
                ''')
            else:
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
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS heartbeats (
                        node_id TEXT PRIMARY KEY,
                        last_seen REAL,
                        is_preferred_leader BOOLEAN
                    )
                ''')
            conn.commit()

    def update_heartbeat(self, node_id: str, last_seen: float, is_preferred: bool):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO heartbeats (node_id, last_seen, is_preferred_leader) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (node_id) DO UPDATE SET last_seen = EXCLUDED.last_seen, is_preferred_leader = EXCLUDED.is_preferred_leader
                ''', (node_id, last_seen, is_preferred))
            else:
                cursor.execute('''
                    INSERT INTO heartbeats (node_id, last_seen, is_preferred_leader) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(node_id) DO UPDATE SET last_seen=excluded.last_seen, is_preferred_leader=excluded.is_preferred_leader
                ''', (node_id, last_seen, is_preferred))
            conn.commit()

    def get_all_heartbeats(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT node_id, last_seen, is_preferred_leader FROM heartbeats')
            rows = cursor.fetchall()
            return [{'node_id': r[0], 'last_seen': r[1], 'is_preferred_leader': bool(r[2])} for r in rows]

    def set_store(self, key: str, value: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            val_str = json.dumps(value)
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO store (key, value) VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                ''', (key, val_str))
            else:
                cursor.execute('''
                    INSERT INTO store (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value
                ''', (key, val_str))
            conn.commit()

    def get_store(self, key: str) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.use_postgres:
                cursor.execute('SELECT value FROM store WHERE key = %s', (key,))
            else:
                cursor.execute('SELECT value FROM store WHERE key = ?', (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return {}

    def insert_trade_history(self, trade: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            args = (
                trade.get("pos_id"), trade.get("symbol"), trade.get("side"),
                trade.get("entry_price", 0), trade.get("exit_price", 0), trade.get("quantity", 0),
                trade.get("net_pnl", 0), trade.get("reason"), trade.get("opened_at"), trade.get("closed_at")
            )
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO trade_history (pos_id, symbol, side, entry_price, exit_price, quantity, net_pnl, reason, opened_at, closed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', args)
            else:
                cursor.execute('''
                    INSERT INTO trade_history (pos_id, symbol, side, entry_price, exit_price, quantity, net_pnl, reason, opened_at, closed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', args)
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
            cursor.execute('DELETE FROM heartbeats')
            conn.commit()

db_manager = DatabaseManager()

def migrate_json_to_db():
    pass

migrate_json_to_db()

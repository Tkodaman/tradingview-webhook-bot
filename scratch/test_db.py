import os
import psycopg2

try:
    conn = psycopg2.connect("postgresql://bot_user:BotStrongPass123!@34.34.50.3:5432/trading_bot", connect_timeout=5)
    print("SUCCESS")
    conn.close()
except Exception as e:
    print(f"FAILED: {e}")

import sqlite3
import json
import time
from config import CACHE_DB, CACHE_EXPIRY_SECONDS

def get_connection():
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    return conn

def cache_get(key: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT value, timestamp FROM cache WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    value, timestamp = row
    if time.time() - timestamp > CACHE_EXPIRY_SECONDS:
        return None
    return json.loads(value)

def cache_set(key: str, value):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
        (key, json.dumps(value), time.time())
    )
    conn.commit()
    conn.close()
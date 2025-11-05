"""Core Database Operations for AgentOS"""

import os
import sqlite3
import threading

DB_DIR = os.path.expanduser("~/.agentos")
DB_PATH = os.path.join(DB_DIR, "runtime.db")
LOGS_DIR = os.path.join(DB_DIR, "logs")
_LOCK = threading.Lock()
_CONN_TIMEOUT = 10.0


def _get_conn():
    """Ensure DB exists and return a SQLite connection with timeout"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=_CONN_TIMEOUT, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize the runtime database if it doesn't exist"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    with _LOCK:
        with _get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    model TEXT,
                    pid INTEGER,
                    status TEXT,
                    started_at TEXT,
                    stopped_at TEXT,
                    log_path TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_agents (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    manifest_path TEXT,
                    task TEXT,
                    schedule_type TEXT,
                    time_config INTEGER,
                    repeat_config INTEGER,
                    next_run TEXT,
                    created_at TEXT
                )
            """)
            conn.commit()


def get_lock():
    """Get the database lock"""
    return _LOCK


def get_connection():
    """Get a database connection"""
    return _get_conn()


# Auto-initialize DB on import
init_db()

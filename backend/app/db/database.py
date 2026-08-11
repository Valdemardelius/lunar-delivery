import sqlite3
from contextlib import contextmanager
from app.core.config import DB_PATH

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self, reset: bool = False):
        with self.connection() as conn:
            if reset:
                for table in ("game_state", "rovers", "orders", "deliveries", "events"):
                    conn.execute(f"DROP TABLE IF EXISTS {table}")
            self._create_tables(conn)

    def _create_tables(self, conn):
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS game_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                day INTEGER NOT NULL,
                money INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                game_over INTEGER NOT NULL,
                order_seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rovers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                battery_max INTEGER NOT NULL,
                battery INTEGER NOT NULL,
                cargo_capacity INTEGER NOT NULL,
                status TEXT NOT NULL,
                repair_days_left INTEGER NOT NULL DEFAULT 0,
                current_order_id TEXT,
                pending_cost INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                zone_id TEXT NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                weight INTEGER NOT NULL,
                reward INTEGER NOT NULL,
                urgency_days INTEGER NOT NULL,
                created_day INTEGER NOT NULL,
                deadline_day INTEGER NOT NULL,
                status TEXT NOT NULL,
                assigned_rover_id TEXT
            );
            CREATE TABLE IF NOT EXISTS deliveries (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                rover_id TEXT NOT NULL,
                day INTEGER NOT NULL,
                success INTEGER NOT NULL,
                earned INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL,
                msg TEXT NOT NULL,
                cls TEXT NOT NULL,
                ts REAL NOT NULL
            );
        """)
import time
from typing import List, Dict

class EventRepository:
    def add(self, conn, day: int, msg: str, cls: str):
        conn.execute(
            "INSERT INTO events (day, msg, cls, ts) VALUES (?,?,?,?)",
            (day, msg, cls, time.time())
        )

    def get_all(self, conn) -> List[Dict]:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT 60"
        ).fetchall()]
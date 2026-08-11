import uuid
from typing import List, Dict

class DeliveryRepository:
    def create(self, conn, order_id: str, rover_id: str, day: int, success: bool, earned: int = 0):
        conn.execute(
            "INSERT INTO deliveries (id, order_id, rover_id, day, success, earned) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), order_id, rover_id, day, int(success), earned)
        )

    def get_all(self, conn) -> List[Dict]:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM deliveries ORDER BY id DESC LIMIT 30"
        ).fetchall()]
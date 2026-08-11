from typing import List, Optional
from app.models.domain import Order, OrderStatus

class OrderRepository:
    def get(self, conn, order_id: str) -> Optional[Order]:
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row:
            return None
        return self._row_to_order(row)

    def get_all_pending_and_in_transit(self, conn, day: int) -> List[Order]:
        rows = conn.execute(
            "SELECT * FROM orders WHERE status IN ('pending','in_transit') OR created_day >= ? ORDER BY created_day DESC",
            (max(1, day - 3),)
        ).fetchall()
        return [self._row_to_order(row) for row in rows]

    def get_pending_by_deadline(self, conn, day: int) -> List[Order]:
        rows = conn.execute(
            "SELECT * FROM orders WHERE status='pending' AND deadline_day<=?",
            (day,)
        ).fetchall()
        return [self._row_to_order(row) for row in rows]

    def _row_to_order(self, row):
        return Order(
            id=row["id"],
            zone_id=row["zone_id"],
            x=row["x"],
            y=row["y"],
            weight=row["weight"],
            reward=row["reward"],
            urgency_days=row["urgency_days"],
            created_day=row["created_day"],
            deadline_day=row["deadline_day"],
            status=OrderStatus(row["status"]),
            assigned_rover_id=row["assigned_rover_id"]
        )

    def update_status(self, conn, order_id: str, status: OrderStatus, assigned_rover_id: Optional[str] = None):
        if assigned_rover_id is not None:
            conn.execute(
                "UPDATE orders SET status=?, assigned_rover_id=? WHERE id=?",
                (status.value, assigned_rover_id, order_id)
            )
        else:
            conn.execute(
                "UPDATE orders SET status=? WHERE id=?",
                (status.value, order_id)
            )

    def create(self, conn, order: Order):
        conn.execute(
            "INSERT INTO orders (id, zone_id, x, y, weight, reward, urgency_days, created_day, deadline_day, status, assigned_rover_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (order.id, order.zone_id, order.x, order.y, order.weight, order.reward,
             order.urgency_days, order.created_day, order.deadline_day,
             order.status.value, order.assigned_rover_id)
        )
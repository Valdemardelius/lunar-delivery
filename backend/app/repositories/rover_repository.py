from typing import List, Optional
from app.models.domain import Rover, RoverStatus

class RoverRepository:
    def get_all(self, conn) -> List[Rover]:
        rows = conn.execute("SELECT * FROM rovers ORDER BY id").fetchall()
        return [self._row_to_rover(row) for row in rows]

    def get(self, conn, rover_id: str) -> Optional[Rover]:
        row = conn.execute("SELECT * FROM rovers WHERE id=?", (rover_id,)).fetchone()
        if not row:
            return None
        return self._row_to_rover(row)

    def _row_to_rover(self, row):
        return Rover(
            id=row["id"],
            name=row["name"],
            battery_max=row["battery_max"],
            battery=row["battery"],
            cargo_capacity=row["cargo_capacity"],
            status=RoverStatus(row["status"]),
            repair_days_left=row["repair_days_left"],
            current_order_id=row["current_order_id"],
            pending_cost=row["pending_cost"]
        )

    def update_status(self, conn, rover_id: str, status: RoverStatus, current_order_id: Optional[str] = None, pending_cost: int = 0):
        conn.execute(
            "UPDATE rovers SET status=?, current_order_id=?, pending_cost=? WHERE id=?",
            (status.value, current_order_id, pending_cost, rover_id)
        )

    def set_broken(self, conn, rover_id: str, battery: int, repair_days: int = 2):
        conn.execute(
            "UPDATE rovers SET status='broken', repair_days_left=?, battery=?, current_order_id=NULL, pending_cost=0 WHERE id=?",
            (repair_days, battery, rover_id)
        )

    def set_idle(self, conn, rover_id: str, battery: int):
        conn.execute(
            "UPDATE rovers SET status='idle', battery=?, current_order_id=NULL, pending_cost=0 WHERE id=?",
            (battery, rover_id)
        )

    def recharge_idle(self, conn, factor: float):
        conn.execute(
            "UPDATE rovers SET battery = MIN(battery_max, battery + CAST(battery_max*? AS INT)) WHERE status='idle'",
            (factor,)
        )

    def auto_repair_broken(self, conn, rover_id: str, battery: int):
        conn.execute(
            "UPDATE rovers SET status='idle', repair_days_left=0, battery=? WHERE id=?",
            (battery, rover_id)
        )

    def update_repair_days(self, conn, rover_id: str, days: int):
        conn.execute("UPDATE rovers SET repair_days_left=? WHERE id=?", (days, rover_id))
import sqlite3
import time
import uuid
import random
from contextlib import contextmanager
from typing import Dict, Any, List, Optional

from config import DB_PATH
from models import GameState, Rover, Order, RoverStatus, OrderStatus
from zones import ZONES, ROVER_TEMPLATES


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

            if not self._game_exists(conn):
                self._seed_new_game(conn)

    def _create_tables(self, conn: sqlite3.Connection):
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

    def _game_exists(self, conn: sqlite3.Connection) -> bool:
        return conn.execute("SELECT 1 FROM game_state WHERE id = 1").fetchone() is not None

    def _seed_new_game(self, conn: sqlite3.Connection):
        conn.execute("DELETE FROM rovers")
        conn.execute("DELETE FROM orders")
        conn.execute("DELETE FROM deliveries")
        conn.execute("DELETE FROM events")
        conn.execute("DELETE FROM game_state")

        conn.execute(
            "INSERT INTO game_state (id, day, money, rating, game_over, order_seq) "
            "VALUES (1, 1, 500, 70, 0, 1)"
        )

        for template in ROVER_TEMPLATES:
            conn.execute(
                "INSERT INTO rovers (id, name, battery_max, battery, cargo_capacity, status, "
                "repair_days_left, current_order_id, pending_cost) VALUES (?,?,?,?,?, 'idle', 0, NULL, 0)",
                (template.id, template.name, template.battery_max, template.battery_max, template.cargo_capacity)
            )

        self.add_event(conn, 1, "— День 1 —", "ev-day")
        self.add_event(
            conn, 1,
            'Добро пожаловать на базу «Скол-9». Распредели роверы и не дай рейтингу базы обнулиться.',
            "ev-info"
        )
        self.generate_orders(conn, day=1, count=3)

    def add_event(self, conn: sqlite3.Connection, day: int, msg: str, cls: str):
        conn.execute(
            "INSERT INTO events (day, msg, cls, ts) VALUES (?,?,?,?)",
            (day, msg, cls, time.time())
        )

    def generate_orders(self, conn: sqlite3.Connection, day: int, count: int):
        from config import (
            IMPOSSIBLE_ORDER_PROBABILITY, WEIGHT_MIN, WEIGHT_MAX,
            IMPOSSIBLE_WEIGHT_MIN, IMPOSSIBLE_WEIGHT_MAX,
            URGENCY_DAYS_MIN, URGENCY_DAYS_MAX
        )

        state = self.get_game_state(conn)
        seq = state.order_seq

        for _ in range(count):
            zone = random.choice(list(ZONES.values()))
            x, y = zone.get_random_point()

            impossible = random.random() < IMPOSSIBLE_ORDER_PROBABILITY
            weight = random.randint(
                IMPOSSIBLE_WEIGHT_MIN if impossible else WEIGHT_MIN,
                IMPOSSIBLE_WEIGHT_MAX if impossible else WEIGHT_MAX
            )
            urgency_days = random.randint(URGENCY_DAYS_MIN, URGENCY_DAYS_MAX)

            reward = round(
                weight * 6 * zone.reward_mult + (6 - urgency_days) * 14 + random.uniform(0, 18)
            )

            order_id = f"o{seq}"
            seq += 1

            conn.execute(
                "INSERT INTO orders (id, zone_id, x, y, weight, reward, urgency_days, created_day, "
                "deadline_day, status, assigned_rover_id) VALUES (?,?,?,?,?,?,?,?,?, 'pending', NULL)",
                (order_id, zone.id, x, y, weight, reward, urgency_days, day, day + urgency_days)
            )

        conn.execute("UPDATE game_state SET order_seq=? WHERE id=1", (seq,))

    def get_game_state(self, conn: sqlite3.Connection) -> GameState:
        row = conn.execute("SELECT * FROM game_state WHERE id=1").fetchone()
        return GameState(
            day=row["day"],
            money=row["money"],
            rating=row["rating"],
            game_over=bool(row["game_over"]),
            order_seq=row["order_seq"]
        )

    def update_game_state(self, conn: sqlite3.Connection, game: GameState):
        conn.execute(
            "UPDATE game_state SET day=?, money=?, rating=?, game_over=? WHERE id=1",
            (game.day, game.money, game.rating, int(game.game_over))
        )

    def get_rovers(self, conn: sqlite3.Connection) -> List[Rover]:
        rows = conn.execute("SELECT * FROM rovers ORDER BY id").fetchall()
        return [
            Rover(
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
            for row in rows
        ]

    def get_rover(self, conn: sqlite3.Connection, rover_id: str) -> Optional[Rover]:
        row = conn.execute("SELECT * FROM rovers WHERE id=?", (rover_id,)).fetchone()
        if not row:
            return None
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

    def get_order(self, conn: sqlite3.Connection, order_id: str) -> Optional[Order]:
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row:
            return None
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

    def get_orders(self, conn: sqlite3.Connection, day: int) -> List[Order]:
        rows = conn.execute(
            "SELECT * FROM orders WHERE status IN ('pending','in_transit') "
            "OR created_day >= ? ORDER BY created_day DESC",
            (max(1, day - 3),)
        ).fetchall()
        return [
            Order(
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
            for row in rows
        ]

    def get_deliveries(self, conn: sqlite3.Connection) -> List[Dict]:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM deliveries ORDER BY id DESC LIMIT 30"
        ).fetchall()]

    def get_events(self, conn: sqlite3.Connection) -> List[Dict]:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT 60"
        ).fetchall()]

    def get_full_state(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        from config import DAYS_TOTAL, BASE_COORDINATES
        from zones import ZONES

        game = self.get_game_state(conn)
        return {
            "game": {
                "day": game.day,
                "money": game.money,
                "rating": game.rating,
                "game_over": game.game_over,
                "days_total": DAYS_TOTAL,
            },
            "rovers": [
                {"id": r.id, "name": r.name, "battery_max": r.battery_max,
                 "battery": r.battery, "cargo_capacity": r.cargo_capacity,
                 "status": r.status.value, "repair_days_left": r.repair_days_left,
                 "current_order_id": r.current_order_id, "pending_cost": r.pending_cost}
                for r in self.get_rovers(conn)
            ],
            "orders": [
                {"id": o.id, "zone_id": o.zone_id, "x": o.x, "y": o.y,
                 "weight": o.weight, "reward": o.reward, "urgency_days": o.urgency_days,
                 "created_day": o.created_day, "deadline_day": o.deadline_day,
                 "status": o.status.value, "assigned_rover_id": o.assigned_rover_id}
                for o in self.get_orders(conn, game.day)
            ],
            "events": self.get_events(conn),
            "deliveries": self.get_deliveries(conn),
            "zones": [{**zone.__dict__, "id": zone.id} for zone in ZONES.values()],
            "base": BASE_COORDINATES,
        }

    def create_delivery(self, conn: sqlite3.Connection, order_id: str, rover_id: str,
                        day: int, success: bool, earned: int = 0):
        conn.execute(
            "INSERT INTO deliveries (id, order_id, rover_id, day, success, earned) "
            "VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), order_id, rover_id, day, int(success), earned)
        )
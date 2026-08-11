import random
from typing import Dict, Any

from fastapi import HTTPException

from app.core.config import (
    DAYS_TOTAL,
    MIN_RATING,
    BATTERY_RECHARGE_FACTOR,
    MIN_ORDERS_PER_DAY,
    MAX_ORDERS_PER_DAY,
)
from app.core.zones import ZONES, ROVER_TEMPLATES
from app.models.domain import GameState, RoverStatus
from app.repositories import (
    GameRepository,
    RoverRepository,
    OrderRepository,
    DeliveryRepository,
    EventRepository,
)
from app.services.rover_service import RoverService
from app.services.order_service import OrderService
from app.services.delivery_service import DeliveryService


class GameService:
    def __init__(
        self,
        game_repo: GameRepository,
        rover_repo: RoverRepository,
        order_repo: OrderRepository,
        delivery_repo: DeliveryRepository,
        event_repo: EventRepository,
        rover_service: RoverService,
        order_service: OrderService,
        delivery_service: DeliveryService,
    ):
        self.game_repo = game_repo
        self.rover_repo = rover_repo
        self.order_repo = order_repo
        self.delivery_repo = delivery_repo
        self.event_repo = event_repo
        self.rover_service = rover_service
        self.order_service = order_service
        self.delivery_service = delivery_service

    def reset_game(self, conn) -> Dict[str, Any]:
        self._seed_new_game(conn)
        return self.get_full_state(conn)

    def _seed_new_game(self, conn):
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
                "repair_days_left, current_order_id, pending_cost) "
                "VALUES (?,?,?,?,?, 'idle', 0, NULL, 0)",
                (
                    template.id,
                    template.name,
                    template.battery_max,
                    template.battery_max,
                    template.cargo_capacity,
                ),
            )

        self.event_repo.add(conn, 1, "— День 1 —", "ev-day")
        self.event_repo.add(
            conn,
            1,
            'Добро пожаловать на базу «Скол-9». Распредели роверы и не дай рейтингу базы обнулиться.',
            "ev-info",
        )

        seq = self.order_service.generate_orders(conn, day=1, count=3, order_seq=1)
        self.game_repo.increment_order_seq(conn, seq)

    def get_full_state(self, conn) -> Dict[str, Any]:
        game = self.game_repo.get_state(conn)
        if game is None:
            self._seed_new_game(conn)
            game = self.game_repo.get_state(conn)

        rovers = self.rover_repo.get_all(conn)
        orders = self.order_repo.get_all_pending_and_in_transit(conn, game.day)
        events = self.event_repo.get_all(conn)
        deliveries = self.delivery_repo.get_all(conn)

        return {
            "game": {
                "day": game.day,
                "money": game.money,
                "rating": game.rating,
                "game_over": game.game_over,
                "days_total": DAYS_TOTAL,
            },
            "rovers": [
                {
                    "id": r.id,
                    "name": r.name,
                    "battery_max": r.battery_max,
                    "battery": r.battery,
                    "cargo_capacity": r.cargo_capacity,
                    "status": r.status.value,
                    "repair_days_left": r.repair_days_left,
                    "current_order_id": r.current_order_id,
                    "pending_cost": r.pending_cost,
                }
                for r in rovers
            ],
            "orders": [
                {
                    "id": o.id,
                    "zone_id": o.zone_id,
                    "x": o.x,
                    "y": o.y,
                    "weight": o.weight,
                    "reward": o.reward,
                    "urgency_days": o.urgency_days,
                    "created_day": o.created_day,
                    "deadline_day": o.deadline_day,
                    "status": o.status.value,
                    "assigned_rover_id": o.assigned_rover_id,
                }
                for o in orders
            ],
            "events": events,
            "deliveries": deliveries,
            "zones": [{**zone.__dict__, "id": zone.id} for zone in ZONES.values()],
            "base": {"x": 400, "y": 250},
        }

    def send_rover(self, conn, order_id: str, rover_id: str) -> Dict[str, Any]:
        game = self.game_repo.get_state(conn)
        if game is None:
            self._seed_new_game(conn)
            game = self.game_repo.get_state(conn)
        if game.game_over:
            raise HTTPException(400, "Игра окончена")

        self.rover_service.send(conn, rover_id, order_id, game.day)
        return self.get_full_state(conn)

    def repair_rover(self, conn, rover_id: str) -> Dict[str, Any]:
        game = self.game_repo.get_state(conn)
        if game is None:
            self._seed_new_game(conn)
            game = self.game_repo.get_state(conn)
        if game.game_over:
            raise HTTPException(400, "Игра окончена")

        self.rover_service.repair(conn, rover_id, game)
        self.game_repo.update_state(conn, game)
        return self.get_full_state(conn)

    def advance_day(self, conn) -> Dict[str, Any]:
        game = self.game_repo.get_state(conn)
        if game is None:
            self._seed_new_game(conn)
            game = self.game_repo.get_state(conn)
        if game.game_over:
            raise HTTPException(400, "Игра окончена")

        day = game.day
        rating = game.rating
        money = game.money

        rovers = self.rover_repo.get_all(conn)

        rating, money = self.delivery_service.process_deliveries(
            conn, rovers, day, rating, money
        )
        self._process_repairs(conn, rovers, day)
        rating = self.delivery_service.process_expired(conn, day, rating)
        self.rover_repo.recharge_idle(conn, BATTERY_RECHARGE_FACTOR)

        new_day = day + 1
        game_over = rating <= 0 or new_day > DAYS_TOTAL

        game.day = min(new_day, DAYS_TOTAL) if game_over and new_day > DAYS_TOTAL else new_day
        game.money = money
        game.rating = max(MIN_RATING, rating)
        game.game_over = game_over
        self.game_repo.update_state(conn, game)

        if not game_over:
            self.event_repo.add(conn, new_day, f"— День {new_day} —", "ev-day")
            orders_count = random.randint(MIN_ORDERS_PER_DAY, MAX_ORDERS_PER_DAY)
            new_seq = self.order_service.generate_orders(conn, new_day, orders_count, game.order_seq)
            self.game_repo.increment_order_seq(conn, new_seq)
        else:
            score = money + rating * 5
            msg = (
                f"☄️ Рейтинг базы обнулился — контракт расторгнут. Итог: {score} очков."
                if rating <= 0
                else f"🌕 Миссия завершена — 15 дней позади. Итог: {score} очков."
            )
            self.event_repo.add(
                conn, day, msg, "ev-bad" if rating <= 0 else "ev-ok"
            )

        return self.get_full_state(conn)

    def _process_repairs(self, conn, rovers, day: int):
        from app.core.config import AUTO_REPAIR_BATTERY_FACTOR

        for rover in rovers:
            if rover.status == RoverStatus.BROKEN:
                left = rover.repair_days_left - 1
                if left <= 0:
                    new_battery = round(rover.battery_max * AUTO_REPAIR_BATTERY_FACTOR)
                    self.rover_repo.auto_repair_broken(conn, rover.id, new_battery)
                    self.event_repo.add(
                        conn,
                        day,
                        f"🔧 {rover.name} самостоятельно восстановлен ремонтной бригадой базы.",
                        "ev-info",
                    )
                else:
                    self.rover_repo.update_repair_days(conn, rover.id, left)
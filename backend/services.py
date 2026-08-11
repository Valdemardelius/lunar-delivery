import random
from typing import Dict, Any, Tuple

from fastapi import HTTPException

from config import (
    REPAIR_COST, MAX_RATING, MIN_RATING, RATING_LOSS_EXPIRED,
    RATING_LOSS_CRASH_BASE, RATING_GAIN_DELIVERY, DAYS_TOTAL,
    BATTERY_RECHARGE_FACTOR, AUTO_REPAIR_BATTERY_FACTOR,
    PAID_REPAIR_BATTERY_FACTOR, MIN_ORDERS_PER_DAY, MAX_ORDERS_PER_DAY
)
from models import RoverStatus, OrderStatus
from zones import ZONES
from database import Database


class GameService:
    def __init__(self, db: Database):
        self.db = db

    def reset_game(self, conn) -> Dict[str, Any]:
        self.db._seed_new_game(conn)
        return self.db.get_full_state(conn)

    def send_rover(self, conn, order_id: str, rover_id: str) -> Dict[str, Any]:
        game = self.db.get_game_state(conn)
        if game.game_over:
            raise HTTPException(400, "Игра окончена")

        order = self.db.get_order(conn, order_id)
        rover = self.db.get_rover(conn, rover_id)

        if not order or not rover:
            raise HTTPException(404, "Заказ или ровер не найден")

        self._validate_send_request(order, rover)

        zone = ZONES[order.zone_id]
        cost = zone.calculate_battery_cost(order.weight)

        self._check_rover_can_handle_order(conn, game, order, rover, zone, cost)

        conn.execute(
            "UPDATE orders SET status='in_transit', assigned_rover_id=? WHERE id=?",
            (rover.id, order.id)
        )
        conn.execute(
            "UPDATE rovers SET status='delivering', current_order_id=?, pending_cost=? WHERE id=?",
            (order.id, cost, rover.id)
        )

        self.db.add_event(
            conn, game.day,
            f'▸ {rover.name} выехал за заказом {order.id} в зону «{zone.name}» '
            f'(риск {int(zone.risk*100)}%, расход {cost}⚡).',
            "ev-info"
        )

        return self.db.get_full_state(conn)

    def _validate_send_request(self, order, rover):
        if order.status != OrderStatus.PENDING:
            raise HTTPException(400, "Заказ уже не свободен")
        if rover.status != RoverStatus.IDLE:
            raise HTTPException(400, f'{rover.name} сейчас недоступен (статус: {rover.status.value}).')

    def _check_rover_can_handle_order(self, conn, game, order, rover, zone, cost):
        if order.weight > rover.cargo_capacity:
            self.db.add_event(
                conn, game.day,
                f'✗ {rover.name} не может взять заказ {order.id}: вес {order.weight}кг '
                f'превышает грузоподъёмность {rover.cargo_capacity}кг.',
                "ev-bad"
            )
            raise HTTPException(400, "Превышена грузоподъёмность ровера")

        if cost > rover.battery:
            self.db.add_event(
                conn, game.day,
                f'✗ {rover.name} не может взять заказ {order.id}: нужно {cost}⚡, '
                f'а в баке {rover.battery}⚡.',
                "ev-bad"
            )
            raise HTTPException(400, "Недостаточно заряда батареи")

    def repair_rover(self, conn, rover_id: str) -> Dict[str, Any]:
        game = self.db.get_game_state(conn)
        rover = self.db.get_rover(conn, rover_id)

        if not rover:
            raise HTTPException(404, "Ровер не найден")

        if rover.status != RoverStatus.BROKEN:
            raise HTTPException(400, "Ровер не сломан")

        if game.money < REPAIR_COST:
            self.db.add_event(
                conn, game.day,
                f'✗ Недостаточно кредитов на ремонт {rover.name} (нужно {REPAIR_COST}₭).',
                "ev-bad"
            )
            raise HTTPException(400, "Недостаточно кредитов")

        new_battery = round(rover.battery_max * PAID_REPAIR_BATTERY_FACTOR)
        conn.execute(
            "UPDATE rovers SET status='idle', repair_days_left=0, battery=? WHERE id=?",
            (new_battery, rover.id)
        )

        game.money -= REPAIR_COST
        self.db.update_game_state(conn, game)

        self.db.add_event(
            conn, game.day,
            f'🔧 {rover.name} отремонтирован за {REPAIR_COST}₭ и снова готов к вылету.',
            "ev-ok"
        )

        return self.db.get_full_state(conn)

    def advance_day(self, conn) -> Dict[str, Any]:
        game = self.db.get_game_state(conn)
        if game.game_over:
            raise HTTPException(400, "Игра окончена")

        day = game.day
        rating = game.rating
        money = game.money

        rovers = self.db.get_rovers(conn)
        rating, money = self._process_deliveries(conn, rovers, day, rating, money)
        self._process_repairs(conn, rovers, day)

        rating = self._process_expired_orders(conn, day, rating)

        self._recharge_idle_rovers(conn)

        new_day = day + 1
        game_over = rating <= 0 or new_day > DAYS_TOTAL

        game.day = min(new_day, DAYS_TOTAL) if game_over and new_day > DAYS_TOTAL else new_day
        game.money = money
        game.rating = max(MIN_RATING, rating)
        game.game_over = game_over

        self.db.update_game_state(conn, game)

        if not game_over:
            self.db.add_event(conn, new_day, f'— День {new_day} —', "ev-day")
            orders_count = random.randint(MIN_ORDERS_PER_DAY, MAX_ORDERS_PER_DAY)
            self.db.generate_orders(conn, new_day, orders_count)
        else:
            score = money + rating * 5
            msg = (
                f'☄️ Рейтинг базы обнулился — контракт расторгнут. Итог: {score} очков.'
                if rating <= 0 else
                f'🌕 Миссия завершена — 15 дней позади. Итог: {score} очков.'
            )
            self.db.add_event(conn, day, msg, "ev-bad" if rating <= 0 else "ev-ok")

        return self.db.get_full_state(conn)

    def _process_deliveries(self, conn, rovers, day: int, rating: int, money: int) -> Tuple[int, int]:
        for rover in rovers:
            if rover.status == RoverStatus.DELIVERING:
                order = self.db.get_order(conn, rover.current_order_id)
                if not order:
                    continue

                zone = ZONES[order.zone_id]
                failed = random.random() < zone.risk
                new_battery = max(0, rover.battery - rover.pending_cost)

                if failed:
                    rating = self._handle_delivery_failure(conn, order, rover, day, rating, new_battery)
                else:
                    rating, money = self._handle_delivery_success(conn, order, rover, day, rating, money, new_battery)

        return rating, money

    def _handle_delivery_failure(self, conn, order, rover, day: int, rating: int, new_battery: int) -> int:
        zone = ZONES[order.zone_id]

        conn.execute("UPDATE orders SET status='failed' WHERE id=?", (order.id,))
        conn.execute(
            "UPDATE rovers SET status='broken', repair_days_left=2, battery=?, "
            "current_order_id=NULL, pending_cost=0 WHERE id=?",
            (new_battery, rover.id)
        )

        rating = max(MIN_RATING, rating - (RATING_LOSS_CRASH_BASE + round(zone.risk * 20)))

        self.db.create_delivery(conn, order.id, rover.id, day, success=False)
        self.db.add_event(
            conn, day,
            f'💥 Авария! {rover.name} потерпел аварию в зоне «{zone.name}», '
            f'груз заказа {order.id} потерян. Ровер повреждён.',
            "ev-bad"
        )

        return rating

    def _handle_delivery_success(self, conn, order, rover, day: int, rating: int,
                                 money: int, new_battery: int) -> Tuple[int, int]:
        conn.execute("UPDATE orders SET status='completed' WHERE id=?", (order.id,))
        conn.execute(
            "UPDATE rovers SET status='idle', battery=?, current_order_id=NULL, pending_cost=0 WHERE id=?",
            (new_battery, rover.id)
        )

        money += order.reward
        rating = min(MAX_RATING, rating + RATING_GAIN_DELIVERY)

        self.db.create_delivery(conn, order.id, rover.id, day, success=True, earned=order.reward)
        self.db.add_event(
            conn, day,
            f'✔ {rover.name} доставил заказ {order.id}: +{order.reward}₭.',
            "ev-ok"
        )

        return rating, money

    def _process_repairs(self, conn, rovers, day: int):
        for rover in rovers:
            if rover.status == RoverStatus.BROKEN:
                left = rover.repair_days_left - 1
                if left <= 0:
                    new_battery = round(rover.battery_max * AUTO_REPAIR_BATTERY_FACTOR)
                    conn.execute(
                        "UPDATE rovers SET status='idle', repair_days_left=0, battery=? WHERE id=?",
                        (new_battery, rover.id)
                    )
                    self.db.add_event(
                        conn, day,
                        f'🔧 {rover.name} самостоятельно восстановлен ремонтной бригадой базы.',
                        "ev-info"
                    )
                else:
                    conn.execute("UPDATE rovers SET repair_days_left=? WHERE id=?", (left, rover.id))

    def _process_expired_orders(self, conn, day: int, rating: int) -> int:
        pending = conn.execute(
            "SELECT * FROM orders WHERE status='pending' AND deadline_day<=?", (day,)
        ).fetchall()

        for order_row in pending:
            conn.execute("UPDATE orders SET status='expired' WHERE id=?", (order_row["id"],))
            rating = max(MIN_RATING, rating - RATING_LOSS_EXPIRED)
            self.db.add_event(
                conn, day,
                f'⏱ Заказ {order_row["id"]} просрочен и отменён клиентом. Рейтинг базы -{RATING_LOSS_EXPIRED}.',
                "ev-bad"
            )

        return rating

    def _recharge_idle_rovers(self, conn):
        conn.execute(
            "UPDATE rovers SET battery = MIN(battery_max, battery + CAST(battery_max*? AS INT)) "
            "WHERE status='idle'",
            (BATTERY_RECHARGE_FACTOR,)
        )
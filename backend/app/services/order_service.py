import random
from app.models.domain import Order, OrderStatus
from app.core.config import (
    IMPOSSIBLE_ORDER_PROBABILITY, WEIGHT_MIN, WEIGHT_MAX,
    IMPOSSIBLE_WEIGHT_MIN, IMPOSSIBLE_WEIGHT_MAX,
    URGENCY_DAYS_MIN, URGENCY_DAYS_MAX
)
from app.core.zones import ZONES
from app.repositories import OrderRepository, EventRepository

class OrderService:
    def __init__(self, order_repo: OrderRepository, event_repo: EventRepository):
        self.order_repo = order_repo
        self.event_repo = event_repo

    def generate_orders(self, conn, day: int, count: int, order_seq: int) -> int:
        seq = order_seq
        for _ in range(count):
            zone = random.choice(list(ZONES.values()))
            x, y = zone.get_random_point()
            impossible = random.random() < IMPOSSIBLE_ORDER_PROBABILITY
            weight = random.randint(
                IMPOSSIBLE_WEIGHT_MIN if impossible else WEIGHT_MIN,
                IMPOSSIBLE_WEIGHT_MAX if impossible else WEIGHT_MAX
            )
            urgency_days = random.randint(URGENCY_DAYS_MIN, URGENCY_DAYS_MAX)
            reward = round(weight * 6 * zone.reward_mult + (6 - urgency_days) * 14 + random.uniform(0, 18))
            order_id = f"o{seq}"
            seq += 1
            order = Order(
                id=order_id,
                zone_id=zone.id,
                x=x, y=y,
                weight=weight,
                reward=reward,
                urgency_days=urgency_days,
                created_day=day,
                deadline_day=day + urgency_days,
                status=OrderStatus.PENDING,
                assigned_rover_id=None
            )
            self.order_repo.create(conn, order)
        return seq
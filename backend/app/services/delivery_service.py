import random
from app.models.domain import RoverStatus, OrderStatus
from app.core.config import RATING_LOSS_CRASH_BASE, RATING_GAIN_DELIVERY, MAX_RATING, MIN_RATING
from app.core.zones import ZONES
from app.repositories import RoverRepository, OrderRepository, DeliveryRepository, EventRepository

class DeliveryService:
    def __init__(self, rover_repo: RoverRepository, order_repo: OrderRepository,
                 delivery_repo: DeliveryRepository, event_repo: EventRepository):
        self.rover_repo = rover_repo
        self.order_repo = order_repo
        self.delivery_repo = delivery_repo
        self.event_repo = event_repo

    def process_deliveries(self, conn, rovers, day: int, rating: int, money: int):
        for rover in rovers:
            if rover.status == RoverStatus.DELIVERING:
                order = self.order_repo.get(conn, rover.current_order_id)
                if not order:
                    continue
                zone = ZONES[order.zone_id]
                failed = random.random() < zone.risk
                new_battery = max(0, rover.battery - rover.pending_cost)
                if failed:
                    rating = self._handle_failure(conn, order, rover, day, rating, new_battery)
                else:
                    rating, money = self._handle_success(conn, order, rover, day, rating, money, new_battery)
        return rating, money

    def _handle_failure(self, conn, order, rover, day: int, rating: int, new_battery: int):
        zone = ZONES[order.zone_id]
        self.order_repo.update_status(conn, order.id, OrderStatus.FAILED)
        self.rover_repo.set_broken(conn, rover.id, new_battery, repair_days=2)
        rating = max(MIN_RATING, rating - (RATING_LOSS_CRASH_BASE + round(zone.risk * 20)))
        self.delivery_repo.create(conn, order.id, rover.id, day, success=False)
        self.event_repo.add(conn, day,
            f'💥 Авария! {rover.name} потерпел аварию в зоне «{zone.name}», груз заказа {order.id} потерян. Ровер повреждён.',
            "ev-bad")
        return rating

    def _handle_success(self, conn, order, rover, day: int, rating: int, money: int, new_battery: int):
        self.order_repo.update_status(conn, order.id, OrderStatus.COMPLETED)
        self.rover_repo.set_idle(conn, rover.id, new_battery)
        money += order.reward
        rating = min(MAX_RATING, rating + RATING_GAIN_DELIVERY)
        self.delivery_repo.create(conn, order.id, rover.id, day, success=True, earned=order.reward)
        self.event_repo.add(conn, day,
            f'✔ {rover.name} доставил заказ {order.id}: +{order.reward}₭.',
            "ev-ok")
        return rating, money

    def process_expired(self, conn, day: int, rating: int):
        from app.core.config import RATING_LOSS_EXPIRED
        expired_orders = self.order_repo.get_pending_by_deadline(conn, day)
        for order in expired_orders:
            self.order_repo.update_status(conn, order.id, OrderStatus.EXPIRED)
            rating = max(MIN_RATING, rating - RATING_LOSS_EXPIRED)
            self.event_repo.add(conn, day,
                f'⏱ Заказ {order.id} просрочен и отменён клиентом. Рейтинг базы -{RATING_LOSS_EXPIRED}.',
                "ev-bad")
        return rating
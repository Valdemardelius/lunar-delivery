from fastapi import HTTPException
from app.models.domain import RoverStatus, OrderStatus
from app.repositories import RoverRepository, OrderRepository, EventRepository
from app.core.config import REPAIR_COST, PAID_REPAIR_BATTERY_FACTOR
from app.core.zones import ZONES

class RoverService:
    def __init__(self, rover_repo: RoverRepository, order_repo: OrderRepository, event_repo: EventRepository):
        self.rover_repo = rover_repo
        self.order_repo = order_repo
        self.event_repo = event_repo

    def send(self, conn, rover_id: str, order_id: str, game_day: int):
        rover = self.rover_repo.get(conn, rover_id)
        order = self.order_repo.get(conn, order_id)
        if not rover or not order:
            raise HTTPException(404, "Ровер или заказ не найден")
        if order.status != OrderStatus.PENDING:
            raise HTTPException(400, "Заказ уже не свободен")
        if rover.status != RoverStatus.IDLE:
            raise HTTPException(400, f"{rover.name} сейчас недоступен (статус: {rover.status.value}).")
        if order.weight > rover.cargo_capacity:
            self.event_repo.add(conn, game_day,
                f'✗ {rover.name} не может взять заказ {order.id}: вес {order.weight}кг превышает грузоподъёмность {rover.cargo_capacity}кг.',
                "ev-bad")
            raise HTTPException(400, "Превышена грузоподъёмность ровера")
        zone = ZONES[order.zone_id]
        cost = zone.calculate_battery_cost(order.weight)
        if cost > rover.battery:
            self.event_repo.add(conn, game_day,
                f'✗ {rover.name} не может взять заказ {order.id}: нужно {cost}⚡, а в баке {rover.battery}⚡.',
                "ev-bad")
            raise HTTPException(400, "Недостаточно заряда батареи")
        self.rover_repo.update_status(conn, rover.id, RoverStatus.DELIVERING, order.id, cost)
        self.order_repo.update_status(conn, order.id, OrderStatus.IN_TRANSIT, rover.id)
        self.event_repo.add(conn, game_day,
            f'▸ {rover.name} выехал за заказом {order.id} в зону «{zone.name}» (риск {int(zone.risk*100)}%, расход {cost}⚡).',
            "ev-info")
        return rover

    def repair(self, conn, rover_id: str, game):
        rover = self.rover_repo.get(conn, rover_id)
        if not rover:
            raise HTTPException(404, "Ровер не найден")
        if rover.status != RoverStatus.BROKEN:
            raise HTTPException(400, "Ровер не сломан")
        if game.money < REPAIR_COST:
            self.event_repo.add(conn, game.day,
                f'✗ Недостаточно кредитов на ремонт {rover.name} (нужно {REPAIR_COST}₭).',
                "ev-bad")
            raise HTTPException(400, "Недостаточно кредитов")
        new_battery = round(rover.battery_max * PAID_REPAIR_BATTERY_FACTOR)
        self.rover_repo.set_idle(conn, rover.id, new_battery)
        game.money -= REPAIR_COST
        self.event_repo.add(conn, game.day,
            f'🔧 {rover.name} отремонтирован за {REPAIR_COST}₭ и снова готов к вылету.',
            "ev-ok")
        return rover
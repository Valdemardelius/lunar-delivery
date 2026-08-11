from app.db.database import Database
from app.repositories import (
    GameRepository, RoverRepository, OrderRepository,
    DeliveryRepository, EventRepository
)
from app.services import GameService, RoverService, OrderService, DeliveryService

_db = Database()

def get_db():
    with _db.connection() as conn:
        yield conn

def get_game_service():
    game_repo = GameRepository()
    rover_repo = RoverRepository()
    order_repo = OrderRepository()
    delivery_repo = DeliveryRepository()
    event_repo = EventRepository()

    rover_service = RoverService(rover_repo, order_repo, event_repo)
    order_service = OrderService(order_repo, event_repo)
    delivery_service = DeliveryService(rover_repo, order_repo, delivery_repo, event_repo)

    return GameService(
        game_repo, rover_repo, order_repo, delivery_repo, event_repo,
        rover_service, order_service, delivery_service
    )
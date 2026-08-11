from dataclasses import dataclass
from enum import Enum
from typing import Optional

class RoverStatus(str, Enum):
    IDLE = "idle"
    DELIVERING = "delivering"
    BROKEN = "broken"

class OrderStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class RoverTemplate:
    id: str
    name: str
    battery_max: int
    cargo_capacity: int

@dataclass
class Rover:
    id: str
    name: str
    battery_max: int
    battery: int
    cargo_capacity: int
    status: RoverStatus
    repair_days_left: int
    current_order_id: Optional[str]
    pending_cost: int

@dataclass
class Order:
    id: str
    zone_id: str
    x: float
    y: float
    weight: int
    reward: int
    urgency_days: int
    created_day: int
    deadline_day: int
    status: OrderStatus
    assigned_rover_id: Optional[str]

@dataclass
class GameState:
    day: int
    money: int
    rating: int
    game_over: bool
    order_seq: int
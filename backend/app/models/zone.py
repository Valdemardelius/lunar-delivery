import math
import random
from dataclasses import dataclass

@dataclass
class Zone:
    id: str
    name: str
    cx: float
    cy: float
    r: float
    risk: float
    base_cost: float
    reward_mult: float
    color: str

    def get_random_point(self) -> tuple[float, float]:
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(0.25, 0.9) * self.r
        return self.cx + math.cos(angle) * dist, self.cy + math.sin(angle) * dist

    def calculate_battery_cost(self, weight: int) -> int:
        return round(self.base_cost + weight * 1.6)
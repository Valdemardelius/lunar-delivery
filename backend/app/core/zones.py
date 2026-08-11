from app.models.zone import Zone
from app.models.domain import RoverTemplate

ZONES = {
    "z1": Zone(
        id="z1",
        name="Море Спокойствия",
        cx=250, cy=190, r=95,
        risk=0.05,
        base_cost=15,
        reward_mult=1.0,
        color="#6fb3d3"
    ),
    "z2": Zone(
        id="z2",
        name="Кратер Тихо",
        cx=560, cy=150, r=75,
        risk=0.15,
        base_cost=30,
        reward_mult=1.4,
        color="#e2a75a"
    ),
    "z3": Zone(
        id="z3",
        name="Тёмная сторона",
        cx=610, cy=370, r=85,
        risk=0.30,
        base_cost=55,
        reward_mult=2.0,
        color="#e2617a"
    ),
    "z4": Zone(
        id="z4",
        name="Равнина Заката",
        cx=170, cy=370, r=78,
        risk=0.10,
        base_cost=22,
        reward_mult=1.2,
        color="#a78fd6"
    ),
}

ROVER_TEMPLATES = [
    RoverTemplate("r1", "Улитка-1", 100, 20),
    RoverTemplate("r2", "Барсук-2", 140, 35),
    RoverTemplate("r3", "Сокол-3", 85, 15),
]
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import Database
from services import GameService
from schemas import SendRequest, RepairRequest

app = FastAPI(title="Lunar Run API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
game_service = GameService(db)


@app.on_event("startup")
def on_startup():
    db.init_db()


@app.get("/api/state")
def get_state():
    with db.connection() as conn:
        return db.get_full_state(conn)


@app.post("/api/reset")
def reset_game():
    with db.connection() as conn:
        return game_service.reset_game(conn)


@app.post("/api/send")
def send_rover(req: SendRequest):
    with db.connection() as conn:
        return game_service.send_rover(conn, req.order_id, req.rover_id)


@app.post("/api/repair")
def repair_rover(req: RepairRequest):
    with db.connection() as conn:
        return game_service.repair_rover(conn, req.rover_id)


@app.post("/api/advance_day")
def advance_day():
    with db.connection() as conn:
        return game_service.advance_day(conn)


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
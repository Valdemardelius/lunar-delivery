from fastapi import APIRouter, Depends
from app.core.dependencies import get_db, get_game_service
from app.schemas.requests import SendRequest, RepairRequest

router = APIRouter(prefix="/api", tags=["game"])

@router.get("/state")
def get_state(conn=Depends(get_db), service=Depends(get_game_service)):
    return service.get_full_state(conn)

@router.post("/reset")
def reset_game(conn=Depends(get_db), service=Depends(get_game_service)):
    return service.reset_game(conn)

@router.post("/send")
def send_rover(req: SendRequest, conn=Depends(get_db), service=Depends(get_game_service)):
    return service.send_rover(conn, req.order_id, req.rover_id)

@router.post("/repair")
def repair_rover(req: RepairRequest, conn=Depends(get_db), service=Depends(get_game_service)):
    return service.repair_rover(conn, req.rover_id)

@router.post("/advance_day")
def advance_day(conn=Depends(get_db), service=Depends(get_game_service)):
    return service.advance_day(conn)

@router.get("/health")
def health():
    return {"status": "ok"}
from pydantic import BaseModel


class SendRequest(BaseModel):
    order_id: str
    rover_id: str


class RepairRequest(BaseModel):
    rover_id: str
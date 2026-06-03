from pydantic import BaseModel, ConfigDict

from .models import ShipmentStatus


class ShipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    tracking_number: str
    courier_name: str
    status: str


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    recipient: str
    payload: str
    status: str
    order_id: int | None
    created_at: datetime

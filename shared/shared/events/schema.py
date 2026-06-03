"""Common event envelope shared across all services.

Every message on the bus is an :class:`Event` serialized as JSON, e.g.::

    {
        "event_type": "OrderCreated",
        "timestamp": "2026-06-03T12:00:00Z",
        "request_id": "…",
        "payload": {"order_id": 123}
    }
"""

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from ..logging import request_id_ctx


class EventType(StrEnum):
    ORDER_CREATED = "OrderCreated"
    ORDER_CANCELLED = "OrderCancelled"
    STOCK_RESERVED = "StockReserved"
    STOCK_UNAVAILABLE = "StockUnavailable"
    STOCK_RELEASED = "StockReleased"
    SHIPMENT_CREATED = "ShipmentCreated"
    SHIPMENT_DELIVERED = "ShipmentDelivered"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Event(BaseModel):
    event_type: str
    timestamp: str = Field(default_factory=_now_iso)
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(cls, event_type: str | EventType, **payload: Any) -> "Event":
        """Build an event, capturing the current request id from context."""
        return cls(
            event_type=str(event_type),
            request_id=request_id_ctx.get(),
            payload=payload,
        )

from enum import StrEnum

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base


class ShipmentStatus(StrEnum):
    CREATED = "CREATED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    tracking_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    courier_name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default=ShipmentStatus.CREATED)

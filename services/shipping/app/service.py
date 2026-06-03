"""Shipping business logic: shipment creation, tracking IDs, status updates."""

import logging
import random
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import cache
from .models import Shipment, ShipmentStatus

logger = logging.getLogger(__name__)

_COURIERS = ["BlueDart", "Delhivery", "FedEx", "DHL", "UPS"]


def _cache_key(shipment_id: int) -> str:
    return f"shipment:{shipment_id}"


def _tracking_number(shipment_id: int) -> str:
    year = datetime.now(timezone.utc).year
    return f"TRK-{year}-{shipment_id:06d}"


async def create_shipment(session: AsyncSession, order_id: int) -> Shipment | None:
    """Create a shipment for an order. Idempotent on order_id."""
    existing = await session.scalar(select(Shipment).where(Shipment.order_id == order_id))
    if existing is not None:
        return existing

    shipment = Shipment(
        order_id=order_id,
        tracking_number="",  # filled in after we have an id
        courier_name=random.choice(_COURIERS),
        status=ShipmentStatus.CREATED,
    )
    session.add(shipment)
    await session.flush()  # assigns shipment.id
    shipment.tracking_number = _tracking_number(shipment.id)
    await session.commit()
    await session.refresh(shipment)
    logger.info(
        "Created shipment %s for order %s (%s)",
        shipment.tracking_number,
        order_id,
        shipment.courier_name,
    )
    return shipment


async def get_shipment(session: AsyncSession, shipment_id: int) -> Shipment | None:
    return await session.get(Shipment, shipment_id)


async def update_status(
    session: AsyncSession, shipment: Shipment, status: ShipmentStatus
) -> Shipment:
    shipment.status = status
    await session.commit()
    await session.refresh(shipment)
    await cache.invalidate(_cache_key(shipment.id))
    return shipment

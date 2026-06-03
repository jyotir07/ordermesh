from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import Identity, get_identity, require_role

from . import service
from .bus import get_broker
from .database import cache, db
from .models import ShipmentStatus
from .schemas import ShipmentOut, ShipmentStatusUpdate
from shared.events import Event, EventType

router = APIRouter(prefix="/shipments", tags=["shipping"])


@router.get("/{shipment_id}", response_model=ShipmentOut)
async def get_shipment(
    shipment_id: int,
    _: Identity = Depends(get_identity),
    session: AsyncSession = Depends(db.session),
):
    cached = await cache.get_json(f"shipment:{shipment_id}")
    if cached is not None:
        return cached
    shipment = await service.get_shipment(session, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    result = ShipmentOut.model_validate(shipment)
    await cache.set_json(f"shipment:{shipment_id}", result.model_dump())
    return result


@router.patch("/{shipment_id}/status", response_model=ShipmentOut)
async def update_shipment_status(
    shipment_id: int,
    payload: ShipmentStatusUpdate,
    _: Identity = Depends(require_role("ADMIN")),
    session: AsyncSession = Depends(db.session),
):
    shipment = await service.get_shipment(session, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    shipment = await service.update_status(session, shipment, payload.status)

    if payload.status == ShipmentStatus.DELIVERED:
        await get_broker().publish(
            Event.create(
                EventType.SHIPMENT_DELIVERED,
                order_id=shipment.order_id,
                tracking_number=shipment.tracking_number,
            )
        )
    return shipment

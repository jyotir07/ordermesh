import re

from app import service
from app.models import ShipmentStatus


async def test_create_shipment_generates_tracking_number(session):
    shipment = await service.create_shipment(session, order_id=42)
    assert shipment is not None
    assert shipment.order_id == 42
    assert shipment.status == ShipmentStatus.CREATED
    assert shipment.courier_name
    assert re.fullmatch(r"TRK-\d{4}-\d{6}", shipment.tracking_number)


async def test_create_shipment_is_idempotent_per_order(session):
    first = await service.create_shipment(session, order_id=7)
    second = await service.create_shipment(session, order_id=7)
    assert first.id == second.id
    assert first.tracking_number == second.tracking_number


async def test_update_status(session):
    shipment = await service.create_shipment(session, order_id=1)
    updated = await service.update_status(session, shipment, ShipmentStatus.DELIVERED)
    assert updated.status == ShipmentStatus.DELIVERED

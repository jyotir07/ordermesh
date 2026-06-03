from app.consumers import _on_stock_reserved
from shared.events import Event, EventType


async def test_stock_reserved_creates_shipment_and_publishes(session, fake_broker):
    event = Event.create(EventType.STOCK_RESERVED, order_id=11, items=[])
    await _on_stock_reserved(event)
    published = fake_broker.events[-1]
    assert published.event_type == "ShipmentCreated"
    assert published.payload["order_id"] == 11
    assert published.payload["tracking_number"].startswith("TRK-")


async def test_stock_reserved_is_idempotent(session, fake_broker):
    event = Event.create(EventType.STOCK_RESERVED, order_id=11, items=[])
    await _on_stock_reserved(event)
    await _on_stock_reserved(event)
    created = [e for e in fake_broker.events if e.event_type == "ShipmentCreated"]
    # Second delivery still publishes, but no duplicate shipment row is created;
    # tracking numbers must match.
    assert created[0].payload["tracking_number"] == created[-1].payload["tracking_number"]

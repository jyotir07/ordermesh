import json

from app import service
from app.consumers import (
    _on_order_created,
    _on_shipment_created,
    _on_shipment_delivered,
    _on_stock_reserved,
)
from shared.events import Event, EventType


async def test_send_notification_persists_record(session):
    n = await service.send_notification(
        session,
        notification_type="Order Confirmation",
        recipient="c@example.com",
        payload={"order_id": 1},
        order_id=1,
    )
    assert n.id is not None
    assert n.status == "SENT"
    assert json.loads(n.payload)["order_id"] == 1


async def test_list_notifications_returns_recent_first(session):
    await service.send_notification(
        session, notification_type="A", recipient="x", payload={}, order_id=1
    )
    await service.send_notification(
        session, notification_type="B", recipient="x", payload={}, order_id=2
    )
    items = await service.list_notifications(session)
    assert [i.type for i in items] == ["B", "A"]


async def test_consumer_handlers_record_notifications(session):
    await _on_order_created(Event.create(EventType.ORDER_CREATED, order_id=5, customer_id=9))
    await _on_stock_reserved(Event.create(EventType.STOCK_RESERVED, order_id=5, customer_id=9))
    await _on_shipment_created(
        Event.create(EventType.SHIPMENT_CREATED, order_id=5, customer_id=9)
    )
    await _on_shipment_delivered(
        Event.create(EventType.SHIPMENT_DELIVERED, order_id=5, customer_id=9)
    )
    items = await service.list_notifications(session)
    types = {i.type for i in items}
    assert types == {
        "Order Confirmation",
        "Stock Reserved",
        "Shipment Created",
        "Shipment Delivered",
    }


async def test_list_notifications_requires_admin(client):
    forbidden = await client.get("/notifications", headers={"X-User-Id": "1", "X-User-Role": "CUSTOMER"})
    assert forbidden.status_code == 403

    ok = await client.get("/notifications", headers={"X-User-Id": "1", "X-User-Role": "ADMIN"})
    assert ok.status_code == 200

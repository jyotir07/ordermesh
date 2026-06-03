from app import service
from app.consumers import _on_order_cancelled, _on_order_created
from app.schemas import ProductCreate
from shared.events import Event, EventType


async def _seed(session, qty=10):
    return await service.create_product(
        session, ProductCreate(sku="SKU1", name="W", quantity_available=qty)
    )


async def test_order_created_reserves_and_publishes_stock_reserved(session, fake_broker):
    product = await _seed(session, qty=10)
    event = Event.create(
        EventType.ORDER_CREATED,
        order_id=1,
        items=[{"product_id": product.id, "quantity": 4}],
    )
    await _on_order_created(event)
    assert fake_broker.events[-1].event_type == "StockReserved"


async def test_order_created_publishes_unavailable_when_short(session, fake_broker):
    product = await _seed(session, qty=2)
    event = Event.create(
        EventType.ORDER_CREATED,
        order_id=1,
        items=[{"product_id": product.id, "quantity": 5}],
    )
    await _on_order_created(event)
    assert fake_broker.events[-1].event_type == "StockUnavailable"


async def test_order_cancelled_releases_and_publishes(session, fake_broker):
    product = await _seed(session, qty=10)
    created = Event.create(
        EventType.ORDER_CREATED,
        order_id=1,
        items=[{"product_id": product.id, "quantity": 4}],
    )
    await _on_order_created(created)
    fake_broker.events.clear()

    await _on_order_cancelled(Event.create(EventType.ORDER_CANCELLED, order_id=1))
    assert fake_broker.events[-1].event_type == "StockReleased"

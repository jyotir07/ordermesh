import pytest

from app import service
from app.models import OrderStatus
from app.schemas import OrderCreate, OrderItemIn


def _payload():
    return OrderCreate(
        items=[
            OrderItemIn(product_id=1, quantity=2, price="10.00"),
            OrderItemIn(product_id=2, quantity=1, price="5.50"),
        ]
    )


async def test_create_order_computes_total_and_publishes(session, fake_broker):
    order = await service.create_order(session, customer_id=7, payload=_payload())
    assert str(order.total_amount) == "25.50"
    assert order.status == OrderStatus.PENDING
    assert order.customer_id == 7
    assert len(order.items) == 2
    assert fake_broker.events[0].event_type == "OrderCreated"
    assert fake_broker.events[0].payload["order_id"] == order.id


async def test_set_status_is_idempotent(session, fake_broker):
    order = await service.create_order(session, customer_id=1, payload=_payload())
    await service.set_status(session, order.id, OrderStatus.CONFIRMED)
    refreshed = await service.get_order(session, order.id)
    assert refreshed.status == OrderStatus.CONFIRMED
    # Applying the same status again is a no-op (no error).
    await service.set_status(session, order.id, OrderStatus.CONFIRMED)


async def test_cancel_order_publishes_cancelled(session, fake_broker):
    order = await service.create_order(session, customer_id=1, payload=_payload())
    fake_broker.events.clear()
    cancelled = await service.cancel_order(session, order)
    assert cancelled.status == OrderStatus.CANCELLED
    assert fake_broker.events[0].event_type == "OrderCancelled"


async def test_list_orders_filters_by_customer(session, fake_broker):
    await service.create_order(session, customer_id=1, payload=_payload())
    await service.create_order(session, customer_id=2, payload=_payload())
    mine = await service.list_orders(session, customer_id=1)
    assert len(mine) == 1
    all_orders = await service.list_orders(session)
    assert len(all_orders) == 2

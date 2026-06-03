from app import service
from app.models import InventoryReservation, Product
from app.schemas import ProductCreate
from sqlalchemy import select


async def _seed(session, sku="SKU1", qty=100):
    product = await service.create_product(
        session, ProductCreate(sku=sku, name="Widget", quantity_available=qty)
    )
    return product


async def test_create_product(session):
    product = await _seed(session, qty=5)
    assert product.id is not None
    assert product.quantity_available == 5


async def test_reserve_decrements_and_records_reservation(session):
    product = await _seed(session, qty=10)
    ok = await service.reserve_for_order(
        session, order_id=1, items=[{"product_id": product.id, "quantity": 3}]
    )
    assert ok is True
    refreshed = await session.get(Product, product.id)
    assert refreshed.quantity_available == 7
    reservation = await session.scalar(
        select(InventoryReservation).where(InventoryReservation.order_id == 1)
    )
    assert reservation.quantity == 3


async def test_reserve_fails_when_insufficient_and_leaves_stock(session):
    product = await _seed(session, qty=2)
    ok = await service.reserve_for_order(
        session, order_id=1, items=[{"product_id": product.id, "quantity": 5}]
    )
    assert ok is False
    refreshed = await session.get(Product, product.id)
    assert refreshed.quantity_available == 2


async def test_reserve_is_idempotent_for_same_order(session):
    product = await _seed(session, qty=10)
    items = [{"product_id": product.id, "quantity": 4}]
    assert await service.reserve_for_order(session, order_id=1, items=items) is True
    # Re-processing the same OrderCreated event must not double-decrement.
    assert await service.reserve_for_order(session, order_id=1, items=items) is True
    refreshed = await session.get(Product, product.id)
    assert refreshed.quantity_available == 6


async def test_reserve_all_or_nothing_across_items(session):
    a = await _seed(session, sku="A", qty=5)
    b = await _seed(session, sku="B", qty=1)
    ok = await service.reserve_for_order(
        session,
        order_id=1,
        items=[{"product_id": a.id, "quantity": 2}, {"product_id": b.id, "quantity": 3}],
    )
    assert ok is False
    # Neither product should be touched.
    assert (await session.get(Product, a.id)).quantity_available == 5
    assert (await session.get(Product, b.id)).quantity_available == 1


async def test_release_restores_stock(session):
    product = await _seed(session, qty=10)
    await service.reserve_for_order(
        session, order_id=1, items=[{"product_id": product.id, "quantity": 4}]
    )
    released = await service.release_for_order(session, order_id=1)
    assert product.id in released
    refreshed = await session.get(Product, product.id)
    assert refreshed.quantity_available == 10

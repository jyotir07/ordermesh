"""Inventory business logic: product management + stock reservation."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import cache
from .models import InventoryReservation, Product
from .schemas import ProductCreate

logger = logging.getLogger(__name__)


def _cache_key(product_id: int) -> str:
    return f"product:{product_id}"


async def create_product(session: AsyncSession, payload: ProductCreate) -> Product:
    product = Product(
        sku=payload.sku, name=payload.name, quantity_available=payload.quantity_available
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def list_products(session: AsyncSession) -> list[Product]:
    return list(await session.scalars(select(Product).order_by(Product.id)))


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    return await session.get(Product, product_id)


async def reserve_for_order(
    session: AsyncSession, order_id: int, items: list[dict]
) -> bool:
    """Atomically reserve stock for every item in an order.

    Returns True if the full order was reserved, False if any item is short.
    Locks the product rows for the duration to avoid oversell under concurrency.
    """
    # Idempotency: if a reservation already exists for this order, treat as done.
    existing = await session.scalar(
        select(InventoryReservation).where(InventoryReservation.order_id == order_id)
    )
    if existing is not None:
        return True

    wanted: dict[int, int] = {}
    for item in items:
        wanted[item["product_id"]] = wanted.get(item["product_id"], 0) + item["quantity"]

    result = await session.execute(
        select(Product).where(Product.id.in_(wanted.keys())).with_for_update()
    )
    products = {p.id: p for p in result.scalars()}

    # Verify availability for all items first.
    for product_id, qty in wanted.items():
        product = products.get(product_id)
        if product is None or product.quantity_available < qty:
            await session.rollback()
            return False

    # Commit the reservation.
    for product_id, qty in wanted.items():
        product = products[product_id]
        product.quantity_available -= qty
        session.add(InventoryReservation(product_id=product_id, order_id=order_id, quantity=qty))

    await session.commit()

    for product_id in wanted:
        await cache.invalidate(_cache_key(product_id))
        product = products[product_id]
        if product.quantity_available < settings.low_stock_threshold:
            logger.warning(
                "LOW STOCK: product %s (%s) at %d units",
                product_id,
                product.sku,
                product.quantity_available,
            )
    return True


async def release_for_order(session: AsyncSession, order_id: int) -> list[int]:
    """Release any reservations held for an order. Returns affected product ids."""
    reservations = list(
        await session.scalars(
            select(InventoryReservation).where(InventoryReservation.order_id == order_id)
        )
    )
    if not reservations:
        return []

    product_ids = {r.product_id for r in reservations}
    result = await session.execute(
        select(Product).where(Product.id.in_(product_ids)).with_for_update()
    )
    products = {p.id: p for p in result.scalars()}
    for reservation in reservations:
        product = products.get(reservation.product_id)
        if product is not None:
            product.quantity_available += reservation.quantity
        await session.delete(reservation)
    await session.commit()

    for product_id in product_ids:
        await cache.invalidate(_cache_key(product_id))
    return list(product_ids)

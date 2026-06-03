"""Order business logic. Pure-ish functions operating on a session; event
publication and cache invalidation are handled here so routes stay thin.
"""

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.events import Event, EventType

from . import bus
from .database import cache
from .models import Order, OrderItem, OrderStatus
from .schemas import OrderCreate

logger = logging.getLogger(__name__)

# Status transitions allowed when an external event arrives.
_CANCELLABLE = {OrderStatus.PENDING, OrderStatus.CONFIRMED}


def _cache_key(order_id: int) -> str:
    return f"order:{order_id}"


async def create_order(session: AsyncSession, customer_id: int, payload: OrderCreate) -> Order:
    total = sum((item.price * item.quantity for item in payload.items), Decimal(0))
    order = Order(customer_id=customer_id, total_amount=total, status=OrderStatus.PENDING)
    order.items = [
        OrderItem(product_id=i.product_id, quantity=i.quantity, price=i.price)
        for i in payload.items
    ]
    session.add(order)
    await session.commit()
    await session.refresh(order)

    await bus.get_broker().publish(
        Event.create(
            EventType.ORDER_CREATED,
            order_id=order.id,
            customer_id=order.customer_id,
            total_amount=str(order.total_amount),
            items=[{"product_id": i.product_id, "quantity": i.quantity} for i in order.items],
        )
    )
    return order


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    return await session.get(Order, order_id)


async def list_orders(
    session: AsyncSession, customer_id: int | None = None
) -> list[Order]:
    stmt = select(Order).order_by(Order.id.desc())
    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
    return list(await session.scalars(stmt))


async def cancel_order(session: AsyncSession, order: Order) -> Order:
    order.status = OrderStatus.CANCELLED
    await session.commit()
    await session.refresh(order)
    await cache.invalidate(_cache_key(order.id))
    await bus.get_broker().publish(
        Event.create(
            EventType.ORDER_CANCELLED,
            order_id=order.id,
            customer_id=order.customer_id,
        )
    )
    return order


async def set_status(session: AsyncSession, order_id: int, status: OrderStatus) -> None:
    """Apply a status change driven by an inbound event (idempotent)."""
    order = await session.get(Order, order_id)
    if order is None:
        logger.warning("set_status: order %s not found", order_id)
        return
    if order.status == status:
        return
    order.status = status
    await session.commit()
    await cache.invalidate(_cache_key(order_id))
    logger.info("Order %s -> %s", order_id, status)

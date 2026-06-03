"""React to order lifecycle events by reserving/releasing stock."""

import logging

from shared.events import Broker, Consumer, Event, EventType

from . import bus, service
from .database import db

logger = logging.getLogger(__name__)


async def _on_order_created(event: Event) -> None:
    order_id = event.payload["order_id"]
    items = event.payload["items"]
    async with db.session_factory() as session:
        reserved = await service.reserve_for_order(session, order_id, items)

    if reserved:
        await bus.get_broker().publish(
            Event.create(EventType.STOCK_RESERVED, order_id=order_id, items=items)
        )
    else:
        await bus.get_broker().publish(
            Event.create(EventType.STOCK_UNAVAILABLE, order_id=order_id)
        )


async def _on_order_cancelled(event: Event) -> None:
    order_id = event.payload["order_id"]
    async with db.session_factory() as session:
        released = await service.release_for_order(session, order_id)
    if released:
        await bus.get_broker().publish(
            Event.create(EventType.STOCK_RELEASED, order_id=order_id, product_ids=released)
        )


def build_consumer(broker: Broker) -> Consumer:
    consumer = Consumer(broker, queue_name="inventory.events")
    consumer.on(EventType.ORDER_CREATED, _on_order_created)
    consumer.on(EventType.ORDER_CANCELLED, _on_order_cancelled)
    return consumer

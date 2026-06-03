"""Inbound events that drive order status transitions."""

import logging

from shared.events import Broker, Consumer, Event, EventType

from . import service
from .database import db
from .models import OrderStatus

logger = logging.getLogger(__name__)


async def _on_stock_reserved(event: Event) -> None:
    async with db.session_factory() as session:
        await service.set_status(session, event.payload["order_id"], OrderStatus.CONFIRMED)


async def _on_stock_unavailable(event: Event) -> None:
    async with db.session_factory() as session:
        await service.set_status(session, event.payload["order_id"], OrderStatus.CANCELLED)


async def _on_shipment_created(event: Event) -> None:
    async with db.session_factory() as session:
        await service.set_status(session, event.payload["order_id"], OrderStatus.SHIPPED)


def build_consumer(broker: Broker) -> Consumer:
    consumer = Consumer(broker, queue_name="order.events")
    consumer.on(EventType.STOCK_RESERVED, _on_stock_reserved)
    consumer.on(EventType.STOCK_UNAVAILABLE, _on_stock_unavailable)
    consumer.on(EventType.SHIPMENT_CREATED, _on_shipment_created)
    return consumer

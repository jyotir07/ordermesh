"""Consume domain events and emit (mock) customer notifications."""

import logging

from shared.events import Broker, Consumer, Event, EventType

from . import service
from .database import db

logger = logging.getLogger(__name__)


def _recipient(event: Event) -> str:
    customer_id = event.payload.get("customer_id", "unknown")
    return f"customer-{customer_id}@example.com"


async def _on_order_created(event: Event) -> None:
    async with db.session_factory() as session:
        await service.send_notification(
            session,
            notification_type="Order Confirmation",
            recipient=_recipient(event),
            payload=event.payload,
            order_id=event.payload.get("order_id"),
        )


async def _on_stock_reserved(event: Event) -> None:
    async with db.session_factory() as session:
        await service.send_notification(
            session,
            notification_type="Stock Reserved",
            recipient=_recipient(event),
            payload=event.payload,
            order_id=event.payload.get("order_id"),
        )


async def _on_shipment_created(event: Event) -> None:
    async with db.session_factory() as session:
        await service.send_notification(
            session,
            notification_type="Shipment Created",
            recipient=_recipient(event),
            payload=event.payload,
            order_id=event.payload.get("order_id"),
        )


async def _on_shipment_delivered(event: Event) -> None:
    async with db.session_factory() as session:
        await service.send_notification(
            session,
            notification_type="Shipment Delivered",
            recipient=_recipient(event),
            payload=event.payload,
            order_id=event.payload.get("order_id"),
        )


def build_consumer(broker: Broker) -> Consumer:
    consumer = Consumer(broker, queue_name="notification.events")
    consumer.on(EventType.ORDER_CREATED, _on_order_created)
    consumer.on(EventType.STOCK_RESERVED, _on_stock_reserved)
    consumer.on(EventType.SHIPMENT_CREATED, _on_shipment_created)
    consumer.on(EventType.SHIPMENT_DELIVERED, _on_shipment_delivered)
    return consumer

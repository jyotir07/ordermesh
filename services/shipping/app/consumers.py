"""Create shipments in response to reserved stock."""

import logging

from shared.events import Broker, Consumer, Event, EventType

from . import bus, service
from .database import db

logger = logging.getLogger(__name__)


async def _on_stock_reserved(event: Event) -> None:
    order_id = event.payload["order_id"]
    async with db.session_factory() as session:
        shipment = await service.create_shipment(session, order_id)
    if shipment is None:
        return
    await bus.get_broker().publish(
        Event.create(
            EventType.SHIPMENT_CREATED,
            order_id=order_id,
            shipment_id=shipment.id,
            tracking_number=shipment.tracking_number,
            courier_name=shipment.courier_name,
        )
    )


def build_consumer(broker: Broker) -> Consumer:
    consumer = Consumer(broker, queue_name="shipping.events")
    consumer.on(EventType.STOCK_RESERVED, _on_stock_reserved)
    return consumer

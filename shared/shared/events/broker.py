"""RabbitMQ connection + topology management via aio-pika.

A single durable topic exchange (``logistics.events``) carries all events; the
routing key is the event_type. A companion dead-letter exchange
(``logistics.dlx``) receives messages that exhaust their retries.
"""

import asyncio
import logging

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message
from aio_pika.abc import AbstractChannel, AbstractExchange, AbstractRobustConnection

from .schema import Event

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "logistics.events"
DLX_NAME = "logistics.dlx"


class Broker:
    """Owns the connection, channel and exchanges for one service."""

    def __init__(self, url: str, service_name: str) -> None:
        self.url = url
        self.service_name = service_name
        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchange: AbstractExchange | None = None
        self.dlx: AbstractExchange | None = None

    async def connect(self, retries: int = 15, delay: float = 3.0) -> None:
        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=10)
                self.exchange = await self.channel.declare_exchange(
                    EXCHANGE_NAME, ExchangeType.TOPIC, durable=True
                )
                self.dlx = await self.channel.declare_exchange(
                    DLX_NAME, ExchangeType.TOPIC, durable=True
                )
                logger.info("Connected to RabbitMQ exchange '%s'", EXCHANGE_NAME)
                return
            except Exception as exc:  # noqa: BLE001 - retry loop
                last_err = exc
                logger.warning(
                    "RabbitMQ connect attempt %d/%d failed: %s", attempt, retries, exc
                )
                await asyncio.sleep(delay)
        raise RuntimeError(f"Could not connect to RabbitMQ after {retries} attempts: {last_err}")

    async def publish(self, event: Event) -> None:
        if self.exchange is None:
            raise RuntimeError("Broker is not connected")
        message = Message(
            body=event.model_dump_json().encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
            headers={"x-event-type": event.event_type},
        )
        await self.exchange.publish(message, routing_key=event.event_type)
        logger.info("Published %s", event.event_type)

    async def close(self) -> None:
        if self.connection is not None:
            await self.connection.close()

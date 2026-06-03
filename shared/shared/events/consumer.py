"""Generic event consumer with retry + dead-letter handling.

Register async handlers per event type, then ``start()`` to bind a durable queue
to the topic exchange. On handler failure the message is re-published with an
incremented retry counter and exponential backoff; once ``MAX_RETRIES`` is
exhausted it is rejected so RabbitMQ routes it to the queue's dead-letter queue.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from ..logging import request_id_ctx
from .broker import DLX_NAME, Broker
from .schema import Event

logger = logging.getLogger(__name__)

Handler = Callable[[Event], Awaitable[None]]

MAX_RETRIES = 3


class Consumer:
    def __init__(self, broker: Broker, queue_name: str) -> None:
        self.broker = broker
        self.queue_name = queue_name
        self.handlers: dict[str, Handler] = {}

    def on(self, event_type: str, handler: Handler) -> "Consumer":
        self.handlers[str(event_type)] = handler
        return self

    async def start(self) -> None:
        channel = self.broker.channel
        if channel is None or self.broker.exchange is None or self.broker.dlx is None:
            raise RuntimeError("Broker is not connected")

        # Dead-letter queue for this consumer.
        dlq = await channel.declare_queue(f"{self.queue_name}.dlq", durable=True)
        await dlq.bind(self.broker.dlx, routing_key=f"{self.queue_name}.dead")

        # Main queue, dead-lettering rejected messages to the DLX.
        queue = await channel.declare_queue(
            self.queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": DLX_NAME,
                "x-dead-letter-routing-key": f"{self.queue_name}.dead",
            },
        )
        for event_type in self.handlers:
            await queue.bind(self.broker.exchange, routing_key=event_type)

        await queue.consume(self._handle)
        logger.info(
            "Consumer '%s' listening for %s", self.queue_name, list(self.handlers)
        )

    async def _handle(self, message: AbstractIncomingMessage) -> None:
        headers = dict(message.headers or {})
        retry = int(headers.get("x-retry", 0))
        token = None
        try:
            event = Event.model_validate_json(message.body)
            if event.request_id:
                token = request_id_ctx.set(event.request_id)
            handler = self.handlers.get(event.event_type)
            if handler is None:
                await message.ack()
                return
            await handler(event)
            await message.ack()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Handler error in '%s': %s", self.queue_name, exc)
            if retry + 1 >= MAX_RETRIES:
                logger.error(
                    "Max retries reached for message in '%s'; dead-lettering",
                    self.queue_name,
                )
                await message.reject(requeue=False)
            else:
                await self._republish(message, retry + 1)
                await message.ack()
        finally:
            if token is not None:
                request_id_ctx.reset(token)

    async def _republish(self, message: AbstractIncomingMessage, retry: int) -> None:
        headers = dict(message.headers or {})
        headers["x-retry"] = retry
        backoff = min(2**retry, 10)
        await asyncio.sleep(backoff)
        new_message = aio_pika.Message(
            body=message.body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type=message.content_type,
            headers=headers,
        )
        await self.broker.exchange.publish(new_message, routing_key=message.routing_key)
        logger.warning("Re-published message to '%s' (retry %d)", self.queue_name, retry)

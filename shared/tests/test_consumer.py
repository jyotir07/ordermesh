import asyncio

import pytest

from shared.events import Event, EventType
from shared.events.consumer import Consumer


class FakeExchange:
    def __init__(self):
        self.published = []

    async def publish(self, message, routing_key):
        self.published.append((message, routing_key))


class FakeBroker:
    def __init__(self):
        self.exchange = FakeExchange()
        self.channel = object()
        self.dlx = object()


class FakeMessage:
    def __init__(self, body: bytes, headers=None, routing_key="OrderCreated"):
        self.body = body
        self.headers = headers or {}
        self.content_type = "application/json"
        self.routing_key = routing_key
        self.acked = False
        self.rejected = False
        self.requeued = None

    async def ack(self):
        self.acked = True

    async def reject(self, requeue=False):
        self.rejected = True
        self.requeued = requeue


def _msg(event: Event, **kw) -> FakeMessage:
    return FakeMessage(event.model_dump_json().encode(), routing_key=event.event_type, **kw)


async def test_handler_dispatched_and_acked():
    broker = FakeBroker()
    seen = []
    consumer = Consumer(broker, "test.queue")

    async def handler(event: Event):
        seen.append(event.payload["order_id"])

    consumer.on(EventType.ORDER_CREATED, handler)
    message = _msg(Event.create(EventType.ORDER_CREATED, order_id=5))
    await consumer._handle(message)
    assert seen == [5]
    assert message.acked


async def test_unknown_event_is_acked_without_handler():
    broker = FakeBroker()
    consumer = Consumer(broker, "test.queue")
    message = _msg(Event.create(EventType.SHIPMENT_DELIVERED, order_id=1))
    await consumer._handle(message)
    assert message.acked
    assert not broker.exchange.published


async def test_failure_dead_letters_after_max_retries():
    broker = FakeBroker()
    consumer = Consumer(broker, "test.queue")

    async def boom(event: Event):
        raise RuntimeError("kaboom")

    consumer.on(EventType.ORDER_CREATED, boom)
    # Already at retry 2 (MAX_RETRIES=3), next failure should reject -> DLQ.
    message = _msg(Event.create(EventType.ORDER_CREATED, order_id=1), headers={"x-retry": 2})
    await consumer._handle(message)
    assert message.rejected
    assert message.requeued is False


async def test_failure_republishes_with_incremented_retry(monkeypatch):
    broker = FakeBroker()
    consumer = Consumer(broker, "test.queue")

    async def _fast_sleep(*_):
        return None

    monkeypatch.setattr(asyncio, "sleep", _fast_sleep)

    async def boom(event: Event):
        raise RuntimeError("kaboom")

    consumer.on(EventType.ORDER_CREATED, boom)
    message = _msg(Event.create(EventType.ORDER_CREATED, order_id=1))
    await consumer._handle(message)
    assert message.acked
    assert len(broker.exchange.published) == 1
    republished, routing_key = broker.exchange.published[0]
    assert routing_key == "OrderCreated"
    assert republished.headers["x-retry"] == 1

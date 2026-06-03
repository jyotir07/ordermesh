import pytest

from shared.events import Broker, Event, EventType


class FakeExchange:
    def __init__(self):
        self.published = []

    async def publish(self, message, routing_key):
        self.published.append((message, routing_key))


async def test_publish_serializes_event_with_routing_key():
    broker = Broker("amqp://unused", "svc")
    broker.exchange = FakeExchange()
    event = Event.create(EventType.ORDER_CREATED, order_id=3)
    await broker.publish(event)

    message, routing_key = broker.exchange.published[0]
    assert routing_key == "OrderCreated"
    assert b"OrderCreated" in message.body
    assert message.headers["x-event-type"] == "OrderCreated"


async def test_publish_without_connection_raises():
    broker = Broker("amqp://unused", "svc")
    with pytest.raises(RuntimeError):
        await broker.publish(Event.create(EventType.ORDER_CREATED, order_id=1))


async def test_close_without_connection_is_safe():
    broker = Broker("amqp://unused", "svc")
    await broker.close()  # no-op, must not raise

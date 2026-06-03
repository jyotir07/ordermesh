from shared.events import Event, EventType


def test_event_create_sets_type_and_payload():
    event = Event.create(EventType.ORDER_CREATED, order_id=7, customer_id=3)
    assert event.event_type == "OrderCreated"
    assert event.payload == {"order_id": 7, "customer_id": 3}
    assert event.timestamp  # default factory populated


def test_event_json_roundtrip():
    event = Event.create(EventType.STOCK_RESERVED, order_id=99)
    restored = Event.model_validate_json(event.model_dump_json())
    assert restored.event_type == "StockReserved"
    assert restored.payload["order_id"] == 99

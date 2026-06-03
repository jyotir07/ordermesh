"""Holds the per-process RabbitMQ broker instance."""

from shared.events import Broker

broker: Broker | None = None


def get_broker() -> Broker:
    if broker is None:
        raise RuntimeError("Broker not initialised")
    return broker

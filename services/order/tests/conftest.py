import os
import pathlib
import tempfile

_DB = pathlib.Path(tempfile.gettempdir()) / "ordermesh_order_test.db"
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_DB.as_posix()}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost/")

import pytest
import pytest_asyncio

from shared.db import Base
from shared.events import Event

from app import bus
from app.database import db


class FakeBroker:
    def __init__(self):
        self.events: list[Event] = []

    async def publish(self, event: Event) -> None:
        self.events.append(event)


@pytest_asyncio.fixture(autouse=True)
async def _reset_db():
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(autouse=True)
def fake_broker():
    bus.broker = FakeBroker()
    return bus.broker


@pytest.fixture(autouse=True)
def _disable_cache(monkeypatch):
    """Avoid real Redis connections during tests (always a cache miss)."""
    from app.database import cache

    async def _miss(*args, **kwargs):
        return None

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(cache, "get_json", _miss)
    monkeypatch.setattr(cache, "set_json", _noop)
    monkeypatch.setattr(cache, "invalidate", _noop)


@pytest_asyncio.fixture
async def session():
    async with db.session_factory() as s:
        yield s

import os
import pathlib
import tempfile

_DB = pathlib.Path(tempfile.gettempdir()) / "ordermesh_notification_test.db"
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_DB.as_posix()}")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost/")

import httpx
import pytest_asyncio
from httpx import ASGITransport

from shared.db import Base

from app.database import db
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def _reset_db():
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def session():
    async with db.session_factory() as s:
        yield s


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

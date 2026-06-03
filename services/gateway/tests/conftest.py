import os
import pathlib
import tempfile

_DB = pathlib.Path(tempfile.gettempdir()) / "ordermesh_gateway_test.db"
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_DB.as_posix()}")
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-bytes-long!!")

import httpx
import pytest
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
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport

from shared.logging import request_id_ctx
from shared.middleware import RequestIDMiddleware


@pytest.fixture
def app():
    application = FastAPI()
    application.add_middleware(RequestIDMiddleware)

    @application.get("/echo")
    async def echo():
        return {"request_id": request_id_ctx.get()}

    return application


async def test_generates_request_id_when_absent(app):
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/echo")
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"]
    assert resp.json()["request_id"] == resp.headers["X-Request-ID"]


async def test_propagates_incoming_request_id(app):
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/echo", headers={"X-Request-ID": "abc-123"})
    assert resp.headers["X-Request-ID"] == "abc-123"
    assert resp.json()["request_id"] == "abc-123"

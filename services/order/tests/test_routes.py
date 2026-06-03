import httpx
import pytest
from httpx import ASGITransport

from app.main import app

CUSTOMER_HEADERS = {"X-User-Id": "10", "X-User-Role": "CUSTOMER"}
OTHER_HEADERS = {"X-User-Id": "20", "X-User-Role": "CUSTOMER"}
ADMIN_HEADERS = {"X-User-Id": "1", "X-User-Role": "ADMIN"}


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_create_and_get_order(client):
    body = {"items": [{"product_id": 1, "quantity": 3, "price": "9.99"}]}
    resp = await client.post("/orders", json=body, headers=CUSTOMER_HEADERS)
    assert resp.status_code == 201
    order = resp.json()
    assert order["status"] == "PENDING"
    assert order["customer_id"] == 10

    got = await client.get(f"/orders/{order['id']}", headers=CUSTOMER_HEADERS)
    assert got.status_code == 200
    assert got.json()["id"] == order["id"]


async def test_customer_cannot_see_others_order(client):
    body = {"items": [{"product_id": 1, "quantity": 1, "price": "1.00"}]}
    created = (await client.post("/orders", json=body, headers=CUSTOMER_HEADERS)).json()

    resp = await client.get(f"/orders/{created['id']}", headers=OTHER_HEADERS)
    assert resp.status_code == 404


async def test_admin_lists_all_orders(client):
    body = {"items": [{"product_id": 1, "quantity": 1, "price": "1.00"}]}
    await client.post("/orders", json=body, headers=CUSTOMER_HEADERS)
    await client.post("/orders", json=body, headers=OTHER_HEADERS)

    resp = await client.get("/orders", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_create_order_validation_error(client):
    resp = await client.post("/orders", json={"items": []}, headers=CUSTOMER_HEADERS)
    assert resp.status_code == 422

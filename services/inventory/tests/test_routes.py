import httpx
import pytest
from httpx import ASGITransport

from app.main import app

ADMIN = {"X-User-Id": "1", "X-User-Role": "ADMIN"}
CUSTOMER = {"X-User-Id": "2", "X-User-Role": "CUSTOMER"}


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_admin_creates_product(client):
    resp = await client.post(
        "/inventory/products",
        json={"sku": "ABC", "name": "Thing", "quantity_available": 50},
        headers=ADMIN,
    )
    assert resp.status_code == 201
    assert resp.json()["sku"] == "ABC"


async def test_customer_cannot_create_product(client):
    resp = await client.post(
        "/inventory/products",
        json={"sku": "ABC", "name": "Thing"},
        headers=CUSTOMER,
    )
    assert resp.status_code == 403


async def test_duplicate_sku_conflicts(client):
    body = {"sku": "DUP", "name": "Thing"}
    assert (await client.post("/inventory/products", json=body, headers=ADMIN)).status_code == 201
    assert (await client.post("/inventory/products", json=body, headers=ADMIN)).status_code == 409


async def test_list_and_get_product(client):
    created = (
        await client.post(
            "/inventory/products",
            json={"sku": "X", "name": "Thing", "quantity_available": 3},
            headers=ADMIN,
        )
    ).json()

    listing = await client.get("/inventory/products", headers=CUSTOMER)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    got = await client.get(f"/inventory/products/{created['id']}", headers=CUSTOMER)
    assert got.status_code == 200
    assert got.json()["sku"] == "X"


async def test_get_missing_product_404(client):
    resp = await client.get("/inventory/products/999", headers=CUSTOMER)
    assert resp.status_code == 404

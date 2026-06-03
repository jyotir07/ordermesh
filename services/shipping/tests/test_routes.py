import httpx
import pytest
from httpx import ASGITransport

from app import service
from app.database import db
from app.main import app

ADMIN = {"X-User-Id": "1", "X-User-Role": "ADMIN"}
CUSTOMER = {"X-User-Id": "2", "X-User-Role": "CUSTOMER"}


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _make_shipment(order_id=1):
    async with db.session_factory() as session:
        return await service.create_shipment(session, order_id=order_id)


async def test_get_shipment(client):
    shipment = await _make_shipment(order_id=5)
    resp = await client.get(f"/shipments/{shipment.id}", headers=CUSTOMER)
    assert resp.status_code == 200
    assert resp.json()["order_id"] == 5


async def test_get_missing_shipment_404(client):
    resp = await client.get("/shipments/999", headers=CUSTOMER)
    assert resp.status_code == 404


async def test_update_status_to_delivered_publishes(client, fake_broker):
    shipment = await _make_shipment(order_id=8)
    resp = await client.patch(
        f"/shipments/{shipment.id}/status", json={"status": "DELIVERED"}, headers=ADMIN
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "DELIVERED"
    assert fake_broker.events[-1].event_type == "ShipmentDelivered"


async def test_update_status_requires_admin(client):
    shipment = await _make_shipment(order_id=9)
    resp = await client.patch(
        f"/shipments/{shipment.id}/status", json={"status": "IN_TRANSIT"}, headers=CUSTOMER
    )
    assert resp.status_code == 403

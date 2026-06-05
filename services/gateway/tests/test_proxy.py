import httpx
import pytest
from httpx import ASGITransport

from app import proxy
from app.config import settings
from app.main import app
from shared.auth import create_access_token


def _token(role="CUSTOMER", uid=5):
    tok = create_access_token(user_id=uid, email="u@e.com", role=role, secret=settings.jwt_secret)
    return {"Authorization": f"Bearer {tok}"}


def _upstream_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "path": request.url.path,
            "uid": request.headers.get("X-User-Id"),
            "role": request.headers.get("X-User-Role"),
            "content_type": request.headers.get("content-type"),
            "body": request.content.decode() or None,
        },
    )


@pytest.fixture
async def client():
    # Mock the downstream client used by the gateway proxy.
    proxy.client = httpx.AsyncClient(transport=httpx.MockTransport(_upstream_handler))
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await proxy.client.aclose()
    proxy.client = None


async def test_authenticated_request_is_forwarded_with_identity(client):
    resp = await client.get("/orders", headers=_token(role="CUSTOMER", uid=5))
    assert resp.status_code == 200
    body = resp.json()
    assert body["path"] == "/orders"
    assert body["uid"] == "5"
    assert body["role"] == "CUSTOMER"


async def test_missing_token_is_rejected(client):
    resp = await client.get("/orders")
    assert resp.status_code in (401, 403)  # HTTPBearer auto_error


async def test_admin_only_route_blocks_customer(client):
    resp = await client.post(
        "/inventory/products", json={"sku": "X", "name": "Y"}, headers=_token(role="CUSTOMER")
    )
    assert resp.status_code == 403


async def test_admin_only_route_allows_admin(client):
    resp = await client.post(
        "/inventory/products", json={"sku": "X", "name": "Y"}, headers=_token(role="ADMIN", uid=1)
    )
    assert resp.status_code == 200
    assert resp.json()["path"] == "/inventory/products"


async def test_shipment_path_forwarded(client):
    resp = await client.get("/shipments/42", headers=_token())
    assert resp.status_code == 200
    assert resp.json()["path"] == "/shipments/42"


async def test_content_type_and_body_are_forwarded(client):
    # Regression: the proxy must preserve Content-Type so downstream services
    # parse the JSON body instead of receiving an opaque string.
    resp = await client.post(
        "/orders", json={"items": [{"product_id": 1}]}, headers=_token()
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["content_type"] == "application/json"
    assert body["body"] == '{"items":[{"product_id":1}]}'

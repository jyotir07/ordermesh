import os

from shared.auth import decode_token


async def test_register_then_login_returns_valid_token(client):
    reg = await client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "secret123", "role": "ADMIN"},
    )
    assert reg.status_code == 201
    assert reg.json()["email"] == "user@example.com"

    login = await client.post(
        "/auth/login", json={"email": "user@example.com", "password": "secret123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    data = decode_token(token, os.environ["JWT_SECRET"])
    assert data.email == "user@example.com"
    assert data.role == "ADMIN"


async def test_duplicate_registration_conflicts(client):
    payload = {"email": "dup@example.com", "password": "secret123"}
    assert (await client.post("/auth/register", json=payload)).status_code == 201
    assert (await client.post("/auth/register", json=payload)).status_code == 409


async def test_login_with_wrong_password_unauthorized(client):
    await client.post(
        "/auth/register", json={"email": "a@example.com", "password": "secret123"}
    )
    resp = await client.post(
        "/auth/login", json={"email": "a@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401


async def test_login_unknown_user_unauthorized(client):
    resp = await client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "whatever"}
    )
    assert resp.status_code == 401

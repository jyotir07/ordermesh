import pytest
from fastapi import HTTPException

from shared.auth import Identity, create_access_token, decode_token, require_role

SECRET = "test-secret"


def test_create_and_decode_token_roundtrip():
    token = create_access_token(user_id=42, email="a@b.com", role="ADMIN", secret=SECRET)
    data = decode_token(token, SECRET)
    assert data.user_id == "42"
    assert data.email == "a@b.com"
    assert data.role == "ADMIN"


def test_decode_invalid_token_raises_401():
    with pytest.raises(HTTPException) as exc:
        decode_token("not-a-jwt", SECRET)
    assert exc.value.status_code == 401


def test_decode_wrong_secret_raises_401():
    token = create_access_token(user_id=1, email="a@b.com", role="CUSTOMER", secret=SECRET)
    with pytest.raises(HTTPException):
        decode_token(token, "other-secret")


def test_require_role_allows_and_blocks():
    checker = require_role("ADMIN")
    admin = Identity(user_id="1", role="ADMIN")
    assert checker(admin) is admin

    customer = Identity(user_id="2", role="CUSTOMER")
    with pytest.raises(HTTPException) as exc:
        checker(customer)
    assert exc.value.status_code == 403

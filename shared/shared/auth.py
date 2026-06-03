"""Authentication helpers.

Two concerns live here:

* JWT issue/verify (used by the API Gateway, which is the trust boundary).
* Identity dependencies for internal services. The gateway validates the JWT and
  forwards ``X-User-Id`` / ``X-User-Role`` headers; internal services trust those
  headers (they are only reachable on the internal compose network).
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

ALGORITHM = "HS256"


class TokenData(BaseModel):
    user_id: str
    email: str
    role: str


def create_access_token(
    *, user_id: int | str, email: str, role: str, secret: str, expires_minutes: int = 60
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(user_id), "email": email, "role": role, "exp": expire}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str) -> TokenData:
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return TokenData(user_id=payload["sub"], email=payload["email"], role=payload["role"])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc


# --- Identity for internal services (header-based, set by the gateway) ---------


class Identity(BaseModel):
    user_id: str
    role: str


def get_identity(
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_user_role: str = Header(..., alias="X-User-Role"),
) -> Identity:
    return Identity(user_id=x_user_id, role=x_user_role)


def require_role(*roles: str):
    """FastAPI dependency factory enforcing that the caller has one of ``roles``."""

    def checker(identity: Identity = Depends(get_identity)) -> Identity:
        if identity.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return identity

    return checker

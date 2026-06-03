"""Gateway-side auth: validate the JWT and expose the caller identity."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.auth import TokenData, decode_token

from .config import settings

_bearer = HTTPBearer(auto_error=True)


async def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> TokenData:
    return decode_token(credentials.credentials, settings.jwt_secret)


async def require_admin(user: TokenData = Depends(current_user)) -> TokenData:
    if user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return user

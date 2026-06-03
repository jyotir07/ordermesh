"""Reverse-proxy helper: forward an incoming request to an internal service,
attaching the authenticated caller's identity as headers.
"""

import httpx
from fastapi import Request, Response

from shared.auth import TokenData
from shared.logging import request_id_ctx

# A single shared client (connection pooling). Created in the app lifespan.
client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    if client is None:
        raise RuntimeError("HTTP client not initialised")
    return client


async def forward(request: Request, base_url: str, path: str, user: TokenData) -> Response:
    url = f"{base_url}{path}"
    headers = {
        "X-User-Id": user.user_id,
        "X-User-Role": user.role,
        "X-Request-ID": request_id_ctx.get(),
    }
    body = await request.body()
    upstream = await get_client().request(
        request.method,
        url,
        params=request.query_params,
        content=body,
        headers=headers,
    )
    # Strip hop-by-hop headers; keep content-type.
    media_type = upstream.headers.get("content-type")
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=media_type,
    )

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from shared.logging import configure_logging
from shared.middleware import RequestIDMiddleware

from . import proxy
from .config import settings
from .routes_auth import router as auth_router
from .routes_proxy import router as proxy_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.service_name)
    proxy.client = httpx.AsyncClient(timeout=15.0)
    yield
    await proxy.client.aclose()


app = FastAPI(title="API Gateway", lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)
app.include_router(auth_router)
app.include_router(proxy_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": settings.service_name}

from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.events import Broker
from shared.logging import configure_logging
from shared.middleware import RequestIDMiddleware

from .config import settings
from .consumers import build_consumer
from .database import db
from .routes import router

_broker: Broker | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _broker
    configure_logging(settings.service_name)
    _broker = Broker(settings.rabbitmq_url, settings.service_name)
    await _broker.connect()
    await build_consumer(_broker).start()
    yield
    await _broker.close()
    await db.dispose()


app = FastAPI(title="Notification Service", lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": settings.service_name}

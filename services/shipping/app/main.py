from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.events import Broker
from shared.logging import configure_logging
from shared.middleware import RequestIDMiddleware

from . import bus
from .config import settings
from .consumers import build_consumer
from .database import cache, db
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.service_name)
    bus.broker = Broker(settings.rabbitmq_url, settings.service_name)
    await bus.broker.connect()
    await build_consumer(bus.broker).start()
    yield
    await bus.broker.close()
    await cache.close()
    await db.dispose()


app = FastAPI(title="Shipping Service", lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": settings.service_name}

"""Structured JSON logging with request-id propagation.

Logs are emitted to stdout as single-line JSON, suitable for future ELK ingestion.
Every record carries: timestamp, level, service, request_id, logger, message.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

# Set per-request by RequestIDMiddleware and propagated into event handlers.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "request_id": request_id_ctx.get(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log, default=str)


def configure_logging(service_name: str, level: int = logging.INFO) -> None:
    """Install the JSON formatter on the root logger. Call once at startup."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(service_name))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    # Quiet noisy third-party loggers.
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("aiormq").setLevel(logging.WARNING)

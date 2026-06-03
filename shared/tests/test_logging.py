import json
import logging

from shared.logging import JsonFormatter, configure_logging, request_id_ctx


def test_json_formatter_includes_required_fields():
    formatter = JsonFormatter("test-svc")
    token = request_id_ctx.set("req-123")
    try:
        record = logging.LogRecord(
            name="x", level=logging.INFO, pathname=__file__, lineno=1,
            msg="hello %s", args=("world",), exc_info=None,
        )
        out = json.loads(formatter.format(record))
    finally:
        request_id_ctx.reset(token)

    assert out["service"] == "test-svc"
    assert out["request_id"] == "req-123"
    assert out["level"] == "INFO"
    assert out["message"] == "hello world"
    assert "timestamp" in out


def test_json_formatter_includes_exception():
    formatter = JsonFormatter("svc")
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="x", level=logging.ERROR, pathname=__file__, lineno=1,
            msg="failed", args=(), exc_info=sys.exc_info(),
        )
    out = json.loads(formatter.format(record))
    assert "exception" in out
    assert "ValueError" in out["exception"]


def test_configure_logging_sets_root_handler():
    configure_logging("svc", level=logging.DEBUG)
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert any(isinstance(h.formatter, JsonFormatter) for h in root.handlers)

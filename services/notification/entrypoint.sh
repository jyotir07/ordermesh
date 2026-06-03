#!/bin/sh
set -e
echo "Running migrations for notification..."
alembic upgrade head
echo "Starting notification service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

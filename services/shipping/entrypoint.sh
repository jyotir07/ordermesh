#!/bin/sh
set -e
echo "Running migrations for shipping..."
alembic upgrade head
echo "Starting shipping service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

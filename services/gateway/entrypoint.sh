#!/bin/sh
set -e
echo "Running migrations for gateway..."
alembic upgrade head
echo "Starting gateway..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

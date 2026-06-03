#!/bin/sh
set -e
echo "Running migrations for inventory..."
alembic upgrade head
echo "Starting inventory service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

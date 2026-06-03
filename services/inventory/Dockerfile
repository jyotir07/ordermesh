# Build context is the repo root (see docker-compose.yml).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY shared /shared
RUN pip install --no-cache-dir /shared

COPY services/inventory/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/inventory/ ./
RUN chmod +x entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]

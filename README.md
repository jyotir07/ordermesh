# OrderMesh — Distributed Logistics & Order Fulfillment Platform

A production-style, event-driven microservices backend simulating an e‑commerce
order fulfillment workflow: customers place orders, stock is reserved, shipments
are created with tracking numbers, and customers are notified — all coordinated
asynchronously over RabbitMQ.


## Architecture

```
            ┌────────────┐
  client ──▶│ API Gateway│  (JWT auth, RBAC, request validation, reverse proxy)
            └─────┬──────┘
       REST  ┌────┴────┬───────────┬───────────┐
             ▼         ▼           ▼            ▼
        ┌────────┐ ┌─────────┐ ┌────────┐ ┌─────────────┐
        │ Order  │ │Inventory│ │Shipping│ │Notification │
        └───┬────┘ └────┬────┘ └───┬────┘ └──────┬──────┘
            │           │          │             │
            └───────────┴────RabbitMQ topic──────┘
                     (logistics.events + DLX/DLQ)
```

**Event flow (happy path):**
`OrderCreated → StockReserved → ShipmentCreated → (notifications)`; insufficient
stock yields `StockUnavailable` → order is `CANCELLED`.

| Service | Responsibility | Publishes | Consumes |
|---|---|---|---|
| **gateway** | Auth (JWT), RBAC, routing | — | — |
| **order** | Orders & items, status lifecycle | OrderCreated, OrderCancelled | StockReserved, StockUnavailable, ShipmentCreated |
| **inventory** | Products, stock reservation | StockReserved, StockUnavailable, StockReleased | OrderCreated, OrderCancelled |
| **shipping** | Shipments, tracking numbers | ShipmentCreated, ShipmentDelivered | StockReserved |
| **notification** | Mock email + history log | — | OrderCreated, StockReserved, ShipmentCreated, ShipmentDelivered |

### Tech
FastAPI · async SQLAlchemy 2.0 + asyncpg · PostgreSQL (database-per-service) ·
Redis (cache-aside) · RabbitMQ (topic exchange, retries, dead-letter queues) ·
Alembic · JWT + bcrypt · Docker Compose · Pytest · GitHub Actions.

## Repository layout

```
shared/                  Installable library: events, broker, auth, db, cache, logging
services/<svc>/app/      FastAPI app (config, models, schemas, service, routes, consumers)
services/<svc>/alembic/  Per-service migrations (run on container start)
infra/postgres/          init script creating the 5 logical databases
docker-compose.yml       Full stack
```

## Running the stack

```bash
cp .env.example .env
docker-compose up --build
```

This starts PostgreSQL, Redis, RabbitMQ and all five services. Each service runs
its Alembic migrations on startup. Once healthy:

- API Gateway → http://localhost:8000  (Swagger UI at `/docs`)
- RabbitMQ management → http://localhost:15672  (user/pass from `.env`)

### Try the end-to-end flow

```bash
# 1. Register an admin + a customer, then log in
curl -X POST localhost:8000/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"admin@x.com","password":"secret123","role":"ADMIN"}'
curl -X POST localhost:8000/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"cust@x.com","password":"secret123"}'
ADMIN=$(curl -s -X POST localhost:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@x.com","password":"secret123"}' | jq -r .access_token)
CUST=$(curl -s -X POST localhost:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"cust@x.com","password":"secret123"}' | jq -r .access_token)

# 2. Admin seeds a product
curl -X POST localhost:8000/inventory/products -H "Authorization: Bearer $ADMIN" \
  -H 'Content-Type: application/json' -d '{"sku":"SKU1","name":"Widget","quantity_available":100}'

# 3. Customer places an order (product_id from step 2)
curl -X POST localhost:8000/orders -H "Authorization: Bearer $CUST" \
  -H 'Content-Type: application/json' \
  -d '{"items":[{"product_id":1,"quantity":2,"price":"19.99"}]}'

# 4. Watch the order become CONFIRMED -> SHIPPED, and a shipment appear
curl localhost:8000/orders/1 -H "Authorization: Bearer $CUST"
curl localhost:8000/shipments/1 -H "Authorization: Bearer $CUST"
```

## Testing

Tests run against SQLite and in-process fakes — **no infra required**.

```bash
python -m venv .venv
. .venv/Scripts/activate          # Windows: .venv\Scripts\activate
pip install ./shared -r requirements-dev.txt
pip install pydantic-settings email-validator   # service runtime deps used by tests

# Run a package's suite with coverage:
cd shared            && pytest --cov=shared
cd services/order    && pytest --cov=app
# ...gateway / inventory / shipping / notification likewise
```

CI (`.github/workflows/ci.yml`) runs every suite with `--cov-fail-under=80`.

## Design notes

- **Event envelope** (`shared/shared/events/schema.py`): `{event_type, timestamp,
  request_id, payload}`. The request id flows from HTTP middleware into events and
  back into consumer logs for traceability.
- **Reliability**: each consumer binds a durable queue; handler failures are
  retried with exponential backoff and dead-lettered after `MAX_RETRIES`.
- **Idempotency**: stock reservation and shipment creation are keyed on
  `order_id`, so redelivered events don't double-apply.
- **Caching**: cache-aside on order/product/shipment lookups; cache failures
  degrade to a miss rather than erroring.
- **Security**: JWT issued by the gateway; internal services trust gateway-set
  `X-User-Id` / `X-User-Role` headers on the private network. Only `ADMIN` can
  manage inventory.

## Stretch goals (not yet implemented)
Distributed tracing / OpenTelemetry, Prometheus + Grafana, rate limiting, circuit
breakers, Saga pattern, AWS (EC2/RDS/ElastiCache) & Kubernetes deployment.

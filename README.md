# Project: Distributed Logistics & Order Fulfillment Platform

## Overview

Build a production-grade logistics and order fulfillment platform inspired by modern supply chain companies such as Locad, ShipBob, and Flexport.

The platform should demonstrate backend engineering best practices including microservices, event-driven communication, asynchronous processing, scalable architecture, and cloud-native deployment.

This project is intended as a portfolio project showcasing backend engineering, distributed systems design, API development, database design, caching, messaging systems, authentication, and DevOps practices.

---

# Business Problem

E-commerce businesses sell products through multiple channels and need a system to:

* Manage inventory across warehouses
* Receive and process customer orders
* Reserve and update stock automatically
* Create shipments
* Track deliveries
* Notify customers about order updates

The platform should simulate this workflow end-to-end.

---

# Tech Stack

Backend:

* FastAPI
* Python 3.12+

Database:

* PostgreSQL

Caching:

* Redis

Message Broker:

* RabbitMQ

ORM:

* SQLAlchemy

Database Migrations:

* Alembic

Authentication:

* JWT Authentication

Containerization:

* Docker
* Docker Compose

Documentation:

* Swagger/OpenAPI

Testing:

* Pytest

Deployment:

* AWS EC2
* AWS RDS
* AWS ElastiCache (optional)

CI/CD:

* GitHub Actions

---

# Architecture

The application should use a microservice architecture.

Services:

1. API Gateway
2. Order Service
3. Inventory Service
4. Shipping Service
5. Notification Service

Communication:

* Synchronous communication via REST APIs
* Asynchronous communication via RabbitMQ events

Example flow:

Customer creates order
→ Order Service validates request
→ Order Created Event published
→ Inventory Service reserves stock
→ Stock Reserved Event published
→ Shipping Service creates shipment
→ Shipment Created Event published
→ Notification Service sends updates

---

# Service 1: Order Service

Responsibilities:

* Create order
* Get order details
* Update order status
* Cancel order
* List orders

Order States:

* PENDING
* CONFIRMED
* SHIPPED
* DELIVERED
* CANCELLED

Database Table:

Orders

* id
* customer_id
* total_amount
* status
* created_at
* updated_at

Order Items

* id
* order_id
* product_id
* quantity
* price

Events:

Publish:

* OrderCreated
* OrderCancelled

Consume:

* StockReserved
* StockUnavailable
* ShipmentCreated

---

# Service 2: Inventory Service

Responsibilities:

* Manage inventory
* Reserve stock
* Release stock
* Update stock levels
* Low stock monitoring

Database Table:

Products

* id
* sku
* name
* quantity_available

Inventory Reservations

* id
* product_id
* order_id
* quantity

Events:

Consume:

* OrderCreated

Publish:

* StockReserved
* StockUnavailable
* StockReleased

Business Logic:

If inventory exists:

* Reserve stock
* Publish StockReserved

Else:

* Publish StockUnavailable

---

# Service 3: Shipping Service

Responsibilities:

* Create shipment
* Assign courier
* Track shipment
* Update shipment status

Shipment Statuses:

* CREATED
* PICKED_UP
* IN_TRANSIT
* DELIVERED

Database Table:

Shipments

* id
* order_id
* tracking_number
* courier_name
* status

Events:

Consume:

* StockReserved

Publish:

* ShipmentCreated
* ShipmentDelivered

Tracking Numbers:

Generate unique tracking IDs automatically.

Example:

TRK-2026-000001

---

# Service 4: Notification Service

Responsibilities:

* Send email notifications
* Log notification history

Events Consumed:

* OrderCreated
* StockReserved
* ShipmentCreated
* ShipmentDelivered

Notification Types:

* Order Confirmation
* Shipment Created
* Shipment Delivered

Initially mock email sending and log notifications in database.

---

# API Gateway

Responsibilities:

* Route requests
* Authentication
* Authorization
* Request validation

Endpoints:

POST /auth/register
POST /auth/login

POST /orders
GET /orders/{id}
GET /orders

POST /inventory/products
GET /inventory/products

GET /shipments/{id}

Gateway should issue JWT tokens.

---

# Redis Usage

Implement Redis caching for:

* Product lookup
* Inventory lookup
* Order lookup

Cache invalidation should happen automatically after updates.

---

# RabbitMQ Events

Create a common event schema.

Example:

{
"event_type": "OrderCreated",
"timestamp": "2026-06-03T12:00:00Z",
"payload": {
"order_id": 123
}
}

Implement publishers and consumers for every service.

Use retry logic and dead-letter queues.

---

# Security

Implement:

* JWT Authentication
* Password hashing with bcrypt
* Role-based access

Roles:

* CUSTOMER
* ADMIN

Only admins can manage inventory.

---

# Logging

Implement structured logging.

Every request should include:

* Request ID
* Timestamp
* Service Name
* Log Level

Store logs in console format suitable for future ELK integration.

---

# Testing

Create:

* Unit tests
* Integration tests

Target:

* Services
* Event processing
* API endpoints

Coverage target:
80%+

---

# Docker

Every service should have:

* Dockerfile
* Environment variables
* Health checks

Provide a docker-compose.yml that runs:

* PostgreSQL
* Redis
* RabbitMQ
* Order Service
* Inventory Service
* Shipping Service
* Notification Service
* API Gateway

Entire system should start with:

docker-compose up

---

# Stretch Goals

If time permits:

1. Distributed tracing
2. OpenTelemetry
3. Prometheus metrics
4. Grafana dashboards
5. AWS deployment
6. Kubernetes deployment
7. Inventory forecasting
8. Rate limiting
9. Circuit breakers
10. Saga pattern for distributed transactions

---

# Expected Outcome

The final project should look like a production-ready backend platform demonstrating:

* FastAPI expertise
* Microservices architecture
* Event-driven systems
* PostgreSQL design
* Redis caching
* RabbitMQ messaging
* Dockerized deployment
* Cloud-ready infrastructure

The codebase should prioritize clean architecture, maintainability, scalability, testing, and industry-standard engineering practices.

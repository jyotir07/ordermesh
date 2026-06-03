-- Creates one logical database per service (database-per-service pattern).
-- Executed automatically by the postgres image on first init.
CREATE DATABASE gateway_db;
CREATE DATABASE order_db;
CREATE DATABASE inventory_db;
CREATE DATABASE shipping_db;
CREATE DATABASE notification_db;

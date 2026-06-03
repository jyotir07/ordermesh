"""initial products and inventory_reservations

Revision ID: 0001
Revises:
Create Date: 2026-06-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("quantity_available", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)

    op.create_table(
        "inventory_reservations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
    )
    op.create_index("ix_inventory_reservations_product_id", "inventory_reservations", ["product_id"])
    op.create_index("ix_inventory_reservations_order_id", "inventory_reservations", ["order_id"])


def downgrade() -> None:
    op.drop_table("inventory_reservations")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_table("products")

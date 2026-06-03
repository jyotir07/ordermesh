"""initial shipments table

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
        "shipments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("tracking_number", sa.String(length=32), nullable=False),
        sa.Column("courier_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="CREATED"),
    )
    op.create_index("ix_shipments_order_id", "shipments", ["order_id"], unique=True)
    op.create_index("ix_shipments_tracking_number", "shipments", ["tracking_number"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_shipments_tracking_number", table_name="shipments")
    op.drop_index("ix_shipments_order_id", table_name="shipments")
    op.drop_table("shipments")

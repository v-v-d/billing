"""receipt_item_type

Revision ID: 99bcad441256
Revises: 77f5794a1db2
Create Date: 2022-08-19 09:26:08.728487

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.

revision = "99bcad441256"
down_revision = "77f5794a1db2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users_films",
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        schema="content",
    )


def downgrade() -> None:
    op.drop_column("users_films", "transaction_id", schema="content")

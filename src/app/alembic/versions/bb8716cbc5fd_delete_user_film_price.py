"""delete_user_film_price

Revision ID: bb8716cbc5fd
Revises: 77f5794a1db2
Create Date: 2022-08-22 21:14:48.526579

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bb8716cbc5fd"
down_revision = "77f5794a1db2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users_films", "price", schema="content")
    op.alter_column("users_films", "is_active", default=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("users_films", "is_active", default=True)
    op.add_column(
        "users_films",
        sa.Column("price", sa.INTEGER(), autoincrement=False, nullable=False),
        schema="content",
    )
    # ### end Alembic commands ###

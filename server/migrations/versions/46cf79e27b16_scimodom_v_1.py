"""scimodom_v.1

Revision ID: 46cf79e27b16
Revises:
Create Date: 2023-08-09 14:43:22.072547

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "46cf79e27b16"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    with open("../dumps/scimodom_v.1.sql") as file:
        op.execute(file.read())


def downgrade() -> None:
    pass

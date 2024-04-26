"""upd_project

Revision ID: 2030d7195a9b
Revises: 1e684fab4e13
Create Date: 2024-04-24 14:10:45.898326

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "2030d7195a9b"
down_revision = "1e684fab4e13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "project", "date_published", existing_type=mysql.DATETIME(), nullable=True
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "project", "date_published", existing_type=mysql.DATETIME(), nullable=False
    )
    # ### end Alembic commands ###

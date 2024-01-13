"""euf_v1.7

Revision ID: 1c61e979733b
Revises: 4cf76bf1e874
Create Date: 2023-12-14 12:20:56.045474

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "1c61e979733b"
down_revision = "4cf76bf1e874"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("data", "ref_base")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "data", sa.Column("ref_base", mysql.VARCHAR(length=1), nullable=False)
    )
    # ### end Alembic commands ###
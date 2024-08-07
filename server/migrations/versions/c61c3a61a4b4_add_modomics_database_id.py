"""add_modomics_database_id

Revision ID: c61c3a61a4b4
Revises: 4926c6c57299
Create Date: 2024-07-15 09:38:26.849020

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c61c3a61a4b4"
down_revision = "4926c6c57299"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("modomics", sa.Column("reference_id", sa.Integer()))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("modomics", "reference_id")
    # ### end Alembic commands ###

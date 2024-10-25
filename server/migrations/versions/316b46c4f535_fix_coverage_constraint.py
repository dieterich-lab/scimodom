"""fix_coverage_constraint

Revision ID: 316b46c4f535
Revises: c61c3a61a4b4
Create Date: 2024-07-23 15:36:21.145946

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "316b46c4f535"
down_revision = "c61c3a61a4b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(constraint_name="cov_strict", table_name="data", type_="check")
    op.create_check_constraint("cov_strict", "data", "coverage >= 0")


def downgrade() -> None:
    op.drop_constraint(constraint_name="cov_strict", table_name="data", type_="check")
    op.create_check_constraint("cov_strict", "data", "coverage > 0")

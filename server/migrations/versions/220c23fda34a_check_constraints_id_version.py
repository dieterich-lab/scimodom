"""check_constraints_id_version

Revision ID: 220c23fda34a
Revises: 316b46c4f535
Create Date: 2024-10-25 13:28:33.712410

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "220c23fda34a"
down_revision = "316b46c4f535"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint("version", "assembly", "LENGTH(version) = 12")
    op.create_check_constraint(
        "version", "assembly_version", "LENGTH(version_num) = 12"
    )
    op.create_check_constraint("version", "annotation", "LENGTH(version) = 12")
    op.create_check_constraint(
        "version", "annotation_version", "LENGTH(version_num) = 12"
    )
    op.create_check_constraint("id", "project", "LENGTH(id) = 8")
    op.create_check_constraint("id", "dataset", "LENGTH(id) = 12")


def downgrade() -> None:
    op.drop_constraint(constraint_name="version", table_name="assembly", type_="check")
    op.drop_constraint(
        constraint_name="version", table_name="assembly_version", type_="check"
    )
    op.drop_constraint(
        constraint_name="version", table_name="annotation", type_="check"
    )
    op.drop_constraint(
        constraint_name="version", table_name="annotation_version", type_="check"
    )
    op.drop_constraint(constraint_name="id", table_name="project", type_="check")
    op.drop_constraint(constraint_name="id", table_name="dataset", type_="check")

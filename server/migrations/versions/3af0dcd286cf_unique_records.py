"""unique_records

Revision ID: 3af0dcd286cf
Revises: cee4ad23a519
Create Date: 2026-06-15 10:38:41.872398

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3af0dcd286cf"
down_revision = "cee4ad23a519"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # keep ix_data_dataset_id
    # op.drop_constraint("fk_data_dataset_id_dataset", "data", type_="foreignkey")
    # op.drop_index("ix_data_dataset_id", table_name="data")
    # op.create_foreign_key("fk_data_dataset", "data", "dataset", ["dataset_id"], ["id"])
    op.create_unique_constraint(
        op.f("uq_data_records"),
        "data",
        ["dataset_id", "modification_id", "chrom", "start", "end", "strand"],
    )


def downgrade() -> None:
    op.drop_constraint(op.f("uq_data_records"), "data", type_="unique")

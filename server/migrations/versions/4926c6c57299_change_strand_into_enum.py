"""Change Strand into Enum

Revision ID: 4926c6c57299
Revises: be4f58630610
Create Date: 2024-06-19 16:00:00.722882

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "4926c6c57299"
down_revision = "be4f58630610"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "data",
        sa.Column(
            "strand_new",
            sa.Enum("FORWARD", "REVERSE", "UNDEFINED"),
            nullable=True,
        ),
    )
    op.execute(
        """
        UPDATE data SET strand_new=CASE
            WHEN strand = '+' THEN 'FORWARD'
            WHEN strand = '-' THEN 'REVERSE'
            ELSE 'UNDEFINED'
        END
    """
    )
    op.alter_column(
        "data",
        "strand",
        new_column_name="strand_old",
        existing_type=sa.String(length=1),
    )
    op.alter_column(
        "data",
        "strand_new",
        nullable=False,
        new_column_name="strand",
        existing_type=sa.Enum("FORWARD", "REVERSE", "UNDEFINED"),
    )
    op.drop_column("data", "strand_old")

    # ### end Alembic commands ###


def downgrade() -> None:
    op.add_column(
        "data",
        sa.Column(
            "strand_old",
            sa.String(length=1),
            nullable=True,
        ),
    )
    op.execute(
        """
        UPDATE data SET strand_old=CASE
            WHEN strand = 'FORWARD' THEN '+'
            WHEN strand = 'REVERSE' THEN '-'
            ELSE '.'
        END
    """
    )
    op.alter_column(
        "data",
        "strand",
        new_column_name="strand_new",
        existing_type=sa.Enum("FORWARD", "REVERSE", "UNDEFINED"),
    )
    op.alter_column(
        "data",
        "strand_old",
        nullable=False,
        new_column_name="strand",
        existing_type=sa.String(length=1),
    )
    op.drop_column("data", "strand_new")

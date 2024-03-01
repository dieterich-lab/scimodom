"""add user table

Revision ID: 1e684fab4e13
Revises: ea1cabad52e4
Create Date: 2024-03-01 11:26:57.308952

"""
import enum

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1e684fab4e13"
down_revision = "ea1cabad52e4"
branch_labels = None
depends_on = None


class UserState(enum.Enum):
    wait_for_confirmation = 0
    active = 1
    password_reset_requested = 2


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "email", sa.String(length=320), nullable=False, index=True, unique=True
        ),
        sa.Column("state", sa.Enum(UserState), default=UserState.wait_for_confirmation),
        sa.Column("password_hash", sa.String(length=64)),
        sa.Column("confirmation_token", sa.String(length=32)),
    )


def downgrade() -> None:
    op.drop_table("user")

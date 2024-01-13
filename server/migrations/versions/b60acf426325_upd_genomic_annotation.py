"""upd_genomic_annotation

Revision ID: b60acf426325
Revises: 2702dc292599
Create Date: 2023-12-06 12:58:29.174047

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "b60acf426325"
down_revision = "2702dc292599"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "genomic_annotation",
        "gene_name",
        existing_type=mysql.VARCHAR(length=32),
        nullable=True,
    )
    op.alter_column(
        "genomic_annotation",
        "gene_id",
        existing_type=mysql.VARCHAR(length=32),
        nullable=True,
    )
    op.alter_column(
        "genomic_annotation",
        "gene_biotype",
        existing_type=mysql.VARCHAR(length=32),
        type_=sa.String(length=255),
        nullable=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "genomic_annotation",
        "gene_biotype",
        existing_type=sa.String(length=255),
        type_=mysql.VARCHAR(length=32),
        nullable=False,
    )
    op.alter_column(
        "genomic_annotation",
        "gene_id",
        existing_type=mysql.VARCHAR(length=32),
        nullable=False,
    )
    op.alter_column(
        "genomic_annotation",
        "gene_name",
        existing_type=mysql.VARCHAR(length=32),
        nullable=False,
    )
    # ### end Alembic commands ###
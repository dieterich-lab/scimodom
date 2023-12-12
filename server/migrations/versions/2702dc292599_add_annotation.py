"""add_annotation

Revision ID: 2702dc292599
Revises: a2107e9c03fc
Create Date: 2023-12-05 13:49:00.435404

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2702dc292599"
down_revision = "a2107e9c03fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "annotation_version",
        sa.Column("version_num", sa.String(length=12), nullable=False),
        sa.PrimaryKeyConstraint("version_num"),
    )
    op.create_table(
        "annotation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("release", sa.Integer(), nullable=False),
        sa.Column("taxa_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=12), nullable=False),
        sa.ForeignKeyConstraint(
            ["taxa_id"],
            ["ncbi_taxa.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "genomic_annotation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("annotation_id", sa.Integer(), nullable=False),
        sa.Column("chrom", sa.String(length=128), nullable=False),
        sa.Column("start", sa.Integer(), nullable=False),
        sa.Column("end", sa.Integer(), nullable=False),
        sa.Column("strand", sa.String(length=1), nullable=False),
        sa.Column("gene_name", sa.String(length=32), nullable=False),
        sa.Column("gene_id", sa.String(length=32), nullable=False),
        sa.Column("gene_biotype", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["annotation_id"],
            ["annotation.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "genomic_region",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data_id", sa.Integer(), nullable=False),
        sa.Column("annotation_id", sa.Integer(), nullable=False),
        sa.Column("feature", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["annotation_id"],
            ["annotation.id"],
        ),
        sa.ForeignKeyConstraint(
            ["data_id"],
            ["data.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("data", sa.Column("annotation_id", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "data", "annotation", ["annotation_id"], ["id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "data", type_="foreignkey")
    op.drop_column("data", "annotation_id")
    op.drop_table("genomic_region")
    op.drop_table("genomic_annotation")
    op.drop_table("annotation")
    op.drop_table("annotation_version")
    # ### end Alembic commands ###

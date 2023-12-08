"""simplify_annotation

Revision ID: 4cf76bf1e874
Revises: b60acf426325
Create Date: 2023-12-08 16:50:38.788583

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "4cf76bf1e874"
down_revision = "b60acf426325"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("genomic_region")
    op.drop_constraint("data_ibfk_2", "data", type_="foreignkey")
    op.drop_column("data", "annotation_id")
    op.add_column(
        "genomic_annotation", sa.Column("data_id", sa.Integer(), nullable=False)
    )
    op.add_column(
        "genomic_annotation", sa.Column("feature", sa.String(length=32), nullable=False)
    )
    op.alter_column(
        "genomic_annotation",
        "gene_name",
        existing_type=mysql.VARCHAR(length=32),
        type_=sa.String(length=128),
        existing_nullable=True,
    )
    op.alter_column(
        "genomic_annotation",
        "gene_id",
        existing_type=mysql.VARCHAR(length=32),
        type_=sa.String(length=128),
        existing_nullable=True,
    )
    op.create_foreign_key(None, "genomic_annotation", "data", ["data_id"], ["id"])
    op.drop_column("genomic_annotation", "end")
    op.drop_column("genomic_annotation", "strand")
    op.drop_column("genomic_annotation", "start")
    op.drop_column("genomic_annotation", "chrom")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "genomic_annotation",
        sa.Column("chrom", mysql.VARCHAR(length=128), nullable=False),
    )
    op.add_column(
        "genomic_annotation",
        sa.Column(
            "start",
            mysql.INTEGER(display_width=11),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "genomic_annotation",
        sa.Column("strand", mysql.VARCHAR(length=1), nullable=False),
    )
    op.add_column(
        "genomic_annotation",
        sa.Column(
            "end", mysql.INTEGER(display_width=11), autoincrement=False, nullable=False
        ),
    )
    op.drop_constraint(None, "genomic_annotation", type_="foreignkey")
    op.alter_column(
        "genomic_annotation",
        "gene_id",
        existing_type=sa.String(length=128),
        type_=mysql.VARCHAR(length=32),
        existing_nullable=True,
    )
    op.alter_column(
        "genomic_annotation",
        "gene_name",
        existing_type=sa.String(length=128),
        type_=mysql.VARCHAR(length=32),
        existing_nullable=True,
    )
    op.drop_column("genomic_annotation", "feature")
    op.drop_column("genomic_annotation", "data_id")
    op.add_column(
        "data",
        sa.Column(
            "annotation_id",
            mysql.INTEGER(display_width=11),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "data_ibfk_2", "data", "annotation", ["annotation_id"], ["id"]
    )
    op.create_table(
        "genomic_region",
        sa.Column(
            "id", mysql.INTEGER(display_width=11), autoincrement=True, nullable=False
        ),
        sa.Column(
            "data_id",
            mysql.INTEGER(display_width=11),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "annotation_id",
            mysql.INTEGER(display_width=11),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("feature", mysql.VARCHAR(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["annotation_id"], ["annotation.id"], name="genomic_region_ibfk_1"
        ),
        sa.ForeignKeyConstraint(["data_id"], ["data.id"], name="genomic_region_ibfk_2"),
        sa.PrimaryKeyConstraint("id"),
        mysql_collate="utf8mb4_general_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    # ### end Alembic commands ###

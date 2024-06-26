"""add_trna

Revision ID: 80658585dbb2
Revises: 622810482837
Create Date: 2024-06-11 14:25:58.871272

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "80658585dbb2"
down_revision = "622810482837"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "sprinzl",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["data_id"], ["data.id"], name=op.f("fk_sprinzl_data_id_data")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sprinzl")),
        sa.UniqueConstraint("data_id", "position", name=op.f("uq_sprinzl_data_id")),
    )
    op.create_index(op.f("ix_sprinzl_data_id"), "sprinzl", ["data_id"], unique=False)
    op.add_column(
        "annotation", sa.Column("source", sa.String(length=128), nullable=False)
    )
    op.drop_constraint("uq_annotation_rtv", "annotation", type_="unique")
    op.create_unique_constraint(
        "uq_annotation_rtv", "annotation", ["release", "taxa_id", "source", "version"]
    )
    op.add_column(
        "assembly", sa.Column("alt_name", sa.String(length=128), nullable=False)
    )
    op.create_unique_constraint(op.f("uq_assembly_alt_name"), "assembly", ["alt_name"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f("uq_assembly_alt_name"), "assembly", type_="unique")
    op.drop_column("assembly", "alt_name")
    op.drop_constraint("uq_annotation_rtv", "annotation", type_="unique")
    op.create_unique_constraint(
        "uq_annotation_rtv", "annotation", ["release", "taxa_id", "version"]
    )
    op.drop_column("annotation", "source")
    op.drop_index(op.f("ix_sprinzl_data_id"), table_name="sprinzl")
    op.drop_table("sprinzl")
    # ### end Alembic commands ###

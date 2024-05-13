"""Add bam_file and user_project_association table

Revision ID: ac1b984c4751
Revises: 6e255bc2f48f
Create Date: 2024-05-07 16:03:52.481486

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ac1b984c4751"
down_revision = "6e255bc2f48f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_project_association",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.String(length=8), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
            name=op.f("fk_user_project_association_project_id_project"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_user_project_association_user_id_user"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_project_association")),
    )
    op.create_index(
        op.f("ix_user_project_association_project_id"),
        "user_project_association",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_project_association_user_id"),
        "user_project_association",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "bam_file",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_file_name", sa.String(length=1024), nullable=False),
        sa.Column("storage_file_name", sa.String(length=256), nullable=False),
        sa.Column("dataset_id", sa.String(length=12), nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_id"], ["dataset.id"], name=op.f("fk_bam_file_dataset_id_dataset")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bam_file")),
        sa.UniqueConstraint(
            "storage_file_name", name=op.f("uq_bam_file_storage_file_name")
        ),
    )
    op.create_index(
        op.f("ix_bam_file_dataset_id"), "bam_file", ["dataset_id"], unique=False
    )


def downgrade() -> None:
    op.drop_constraint("fk_bam_file_dataset_id_dataset", "bam_file", type_="foreignkey")
    op.drop_index(op.f("ix_bam_file_dataset_id"), table_name="bam_file")
    op.drop_table("bam_file")

    op.drop_constraint(
        "fk_user_project_association_project_id_project",
        "user_project_association",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_user_project_association_user_id_user",
        "user_project_association",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_user_project_association_user_id"),
        table_name="user_project_association",
    )
    op.drop_index(
        op.f("ix_user_project_association_project_id"),
        table_name="user_project_association",
    )
    op.drop_table("user_project_association")

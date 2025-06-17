"""euf_v2_data

Revision ID: 6faa5954d595
Revises: c3c761aca33b
Create Date: 2025-06-20 12:25:48.617935

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "6faa5954d595"
down_revision = "c3c761aca33b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # convert score to coverage for existing data
    op.add_column(
        "data",
        sa.Column(
            "score_new",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.execute("UPDATE data SET score_new=coverage")
    # remove old score - not reversible!
    op.drop_constraint(op.f("ck_data_score"), "data", type_="check")
    op.drop_constraint(op.f("ck_data_score_max"), "data", type_="check")
    op.drop_index(op.f("ix_data_score"), table_name="data")
    op.drop_column("data", "score")
    op.alter_column(
        "data",
        "score_new",
        nullable=False,
        new_column_name="score",
        existing_type=sa.Integer(),
    )
    op.create_index(op.f("ix_data_score"), "data", ["score"], unique=False)
    op.create_check_constraint(
        op.f("ck_data_score_strict"),
        "data",
        "score > 0",
    )
    # coverage
    # cf. revision 316b46c4f535 - name remained unchanged but constraint was modified
    op.drop_constraint(op.f("ck_data_cov_strict"), "data", type_="check")
    op.create_check_constraint(
        op.f("ck_data_cov_strict"),
        "data",
        "coverage > 0",
    )
    # frequency
    op.drop_constraint(op.f("ck_data_freq_strict"), "data", type_="check")
    op.create_check_constraint(
        op.f("ck_data_freq_min"),
        "data",
        "frequency >= 0",
    )
    op.alter_column(
        "data",
        "frequency",
        existing_type=mysql.INTEGER(display_width=11),
        type_=sa.Numeric(precision=5, scale=2, asdecimal=True),
        existing_nullable=False,
    )


def downgrade() -> None:
    # WARNING: data loss will occur for new data added after upgrade.
    # For existing data, it is not possible to retrieve the "old score" definition
    op.execute("UPDATE data SET score=1000 WHERE score>1000")
    op.drop_constraint(op.f("ck_data_score_strict"), "data", type_="check")
    op.create_check_constraint(
        op.f("ck_data_score"),
        "data",
        "score >= 0",
    )
    op.create_check_constraint(
        op.f("ck_data_score_max"),
        "data",
        "score <= 1000",
    )
    # cf. revision 316b46c4f535 - name remained unchanged but constraint was modified
    op.drop_constraint(op.f("ck_data_cov_strict"), "data", type_="check")
    op.create_check_constraint(
        op.f("ck_data_cov_strict"),
        "data",
        "coverage >= 0",
    )
    # WARNING: data loss will occur for new data added after upgrade.
    op.execute("UPDATE data SET frequency=ROUND(frequency)")
    op.execute("UPDATE data SET frequency=1 WHERE frequency=0")
    op.drop_constraint(op.f("ck_data_freq_min"), "data", type_="check")
    op.create_check_constraint(
        op.f("ck_data_freq_strict"),
        "data",
        "frequency > 0",
    )
    op.alter_column(
        "data",
        "frequency",
        existing_type=sa.Numeric(precision=5, scale=2, asdecimal=True),
        type_=mysql.INTEGER(display_width=11),
        existing_nullable=False,
    )

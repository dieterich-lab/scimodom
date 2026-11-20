"""annotation_references_assembly

An annotation is a set of features in the coordinate system of an
assembly, but `annotation` only referenced a taxa. Which assembly an
annotation belonged to was carried by the file system: the release
directory was built under the name of whichever assembly was current
when the path was constructed, so bumping `assembly_version` silently
moved existing annotations onto the new assembly.

Reference the assembly instead, and drop `taxa_id`, which is reached
through it. The backfill is unambiguous while there is one current
assembly per taxa; it stops being so once an upgrade introduces a
second generation.

`annotation_release` records where a provider serves the data of one
release. Ensembl publishes the mapping of a release onto its archive
as an HTML list only, so it cannot be derived.

Revision ID: 7c1f2b9ad540
Revises: b39760c14af1
Create Date: 2026-11-20 09:12:44.108233

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7c1f2b9ad540"
down_revision = "b39760c14af1"
branch_labels = None
depends_on = None


# Ensembl archives, cf. https://www.ensembl.org/info/website/archives/
# Only needed to backfill `annotation_release` for the releases already
# in the database; afterwards the mapping is seeded and maintained in
# `annotation_release.csv`.
ENSEMBL_ARCHIVES = {
    105: "dec2021",
    106: "apr2022",
    107: "jul2022",
    108: "oct2022",
    109: "feb2023",
    110: "jul2023",
    111: "jan2024",
    112: "may2024",
    113: "oct2024",
    114: "may2025",
    115: "sep2025",
    116: "jun2026",
}


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        "annotation_release",
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("release", sa.Integer(), nullable=False),
        sa.Column("archive", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint(
            "source", "release", name=op.f("pk_annotation_release")
        ),
    )

    # backfill: one row per release already in use. An Ensembl release
    # does have an archive, so not knowing it is a gap worth stopping
    # for; another provider may genuinely have none, and gets a null.
    in_use = bind.execute(
        sa.text("SELECT DISTINCT source, `release` FROM annotation")
    ).fetchall()
    unknown = [
        (source, release)
        for source, release in in_use
        if source == "ensembl" and release not in ENSEMBL_ARCHIVES
    ]
    if unknown:
        listed = ", ".join(f"{source} {release}" for source, release in unknown)
        raise RuntimeError(
            f"Cannot determine the Ensembl archive of: {listed}. Insert the "
            "row(s) into 'annotation_release' by hand, then run this "
            "migration again."
        )
    for source, release in in_use:
        bind.execute(
            sa.text(
                "INSERT INTO annotation_release (source, `release`, archive) "
                "VALUES (:source, :release, :archive)"
            ),
            {
                "source": source,
                "release": release,
                "archive": (ENSEMBL_ARCHIVES[release] if source == "ensembl" else None),
            },
        )

    # expand
    op.add_column("annotation", sa.Column("assembly_id", sa.Integer(), nullable=True))

    # backfill: the assembly of an annotation is the one that was
    # current for its taxa, which is what the file system assumed
    bind.execute(
        sa.text(
            """
            UPDATE annotation a
            JOIN assembly s
              ON s.taxa_id = a.taxa_id
             AND s.version = (SELECT version_num FROM assembly_version)
            SET a.assembly_id = s.id
            """
        )
    )
    orphaned = bind.execute(
        sa.text(
            "SELECT id, taxa_id, `release`, source FROM annotation "
            "WHERE assembly_id IS NULL"
        )
    ).fetchall()
    if orphaned:
        listed = ", ".join(
            f"annotation {row[0]} (taxa {row[1]}, {row[3]} {row[2]})"
            for row in orphaned
        )
        raise RuntimeError(
            f"No current assembly for: {listed}. Every annotation must belong "
            "to an assembly of the current assembly version."
        )

    # contract
    op.alter_column(
        "annotation",
        "assembly_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_index(
        op.f("ix_annotation_assembly_id"), "annotation", ["assembly_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_annotation_assembly_id_assembly"),
        "annotation",
        "assembly",
        ["assembly_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_annotation_annotation_release",
        "annotation",
        "annotation_release",
        ["source", "release"],
        ["source", "release"],
    )

    # one annotation per assembly, source and generation. The release
    # is deliberately not part of the key: two releases of the same
    # source must not both be current on the same assembly, which
    # nothing but an upgrade remembering to retire the old row would
    # otherwise prevent.
    duplicated = bind.execute(
        sa.text(
            """
            SELECT assembly_id, source, version, COUNT(*) AS n
            FROM annotation
            GROUP BY assembly_id, source, version
            HAVING n > 1
            """
        )
    ).fetchall()
    if duplicated:
        listed = ", ".join(
            f"assembly {row[0]} / {row[1]} / version {row[2]} ({row[3]} rows)"
            for row in duplicated
        )
        raise RuntimeError(
            f"More than one annotation for: {listed}. Only one annotation "
            "per assembly, source and version may exist; retire the "
            "superseded one by changing its version, then run this "
            "migration again."
        )
    op.drop_constraint("uq_annotation_rtv", "annotation", type_="unique")
    op.create_unique_constraint(
        "uq_annotation_asv",
        "annotation",
        ["assembly_id", "source", "version"],
    )

    op.drop_constraint(
        "fk_annotation_taxa_id_ncbi_taxa", "annotation", type_="foreignkey"
    )
    op.drop_index("ix_annotation_taxa_id", table_name="annotation")
    op.drop_column("annotation", "taxa_id")


def downgrade() -> None:
    bind = op.get_bind()

    op.add_column("annotation", sa.Column("taxa_id", sa.Integer(), nullable=True))
    bind.execute(
        sa.text(
            """
            UPDATE annotation a
            JOIN assembly s ON s.id = a.assembly_id
            SET a.taxa_id = s.taxa_id
            """
        )
    )
    op.alter_column("annotation", "taxa_id", existing_type=sa.Integer(), nullable=False)
    op.create_index("ix_annotation_taxa_id", "annotation", ["taxa_id"], unique=False)
    op.create_foreign_key(
        "fk_annotation_taxa_id_ncbi_taxa",
        "annotation",
        "ncbi_taxa",
        ["taxa_id"],
        ["id"],
    )

    op.drop_constraint("uq_annotation_asv", "annotation", type_="unique")
    op.create_unique_constraint(
        "uq_annotation_rtv", "annotation", ["release", "taxa_id", "source", "version"]
    )

    op.drop_constraint(
        "fk_annotation_annotation_release", "annotation", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_annotation_assembly_id_assembly"), "annotation", type_="foreignkey"
    )
    op.drop_index(op.f("ix_annotation_assembly_id"), table_name="annotation")
    op.drop_column("annotation", "assembly_id")

    op.drop_table("annotation_release")

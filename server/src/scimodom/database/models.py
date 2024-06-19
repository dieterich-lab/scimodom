import enum
from datetime import datetime
from typing import List, Optional
from scimodom.utils.common_dto import Strand

from sqlalchemy import (
    String,
    Text,
    DateTime,
    Index,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scimodom.database.database import Base


class RNAType(Base):
    """RNA types (nomenclature)"""

    __tablename__ = "rna_type"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    modifications: Mapped[List["Modification"]] = relationship(
        back_populates="inst_rna"
    )


class Modomics(Base):
    """Modified residues"""

    __tablename__ = "modomics"

    id: Mapped[str] = mapped_column(
        String(128), primary_key=True, autoincrement=False
    )  # MODOMICS code
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    short_name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    moiety: Mapped[str] = mapped_column(String(32), nullable=False)

    modifications: Mapped[List["Modification"]] = relationship(
        back_populates="inst_modomics"
    )
    # datas: Mapped[List["Data"]] = relationship(back_populates="inst_modomics")


class Modification(Base):
    """Modification (RNA type)"""

    __tablename__ = "modification"

    id: Mapped[int] = mapped_column(primary_key=True)
    modomics_id: Mapped[str] = mapped_column(ForeignKey("modomics.id"), index=True)
    rna: Mapped[str] = mapped_column(ForeignKey("rna_type.id"))

    __table_args__ = (UniqueConstraint(modomics_id, rna),)

    inst_modomics: Mapped["Modomics"] = relationship(back_populates="modifications")
    inst_rna: Mapped["RNAType"] = relationship(back_populates="modifications")

    selections: Mapped[List["Selection"]] = relationship(
        back_populates="inst_modification"
    )
    datas: Mapped[List["Data"]] = relationship(back_populates="inst_modification")
    associations: Mapped[List["DatasetModificationAssociation"]] = relationship(
        back_populates="inst_modification"
    )


class DetectionMethod(Base):
    """Detection methods (nomenclature)"""

    __tablename__ = "method"

    id: Mapped[str] = mapped_column(String(8), primary_key=True, autoincrement=False)
    cls: Mapped[str] = mapped_column(String(32), nullable=False)
    meth: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    technologies: Mapped[List["DetectionTechnology"]] = relationship(
        back_populates="inst_method"
    )


class DetectionTechnology(Base):
    """Detection methods (technology)"""

    __tablename__ = "technology"

    id: Mapped[int] = mapped_column(primary_key=True)
    method_id: Mapped[int] = mapped_column(ForeignKey("method.id"), index=True)
    tech: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    __table_args__ = (UniqueConstraint(method_id, tech),)

    inst_method: Mapped["DetectionMethod"] = relationship(back_populates="technologies")

    selections: Mapped[List["Selection"]] = relationship(
        back_populates="inst_technology"
    )
    datasets: Mapped[List["Dataset"]] = relationship(back_populates="inst_technology")


class Taxonomy(Base):
    """Taxonomic rank (up to phylum)"""

    __tablename__ = "taxonomy"

    id: Mapped[str] = mapped_column(String(8), primary_key=True, autoincrement=False)
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    kingdom: Mapped[str] = mapped_column(String(32), nullable=True)
    phylum: Mapped[str] = mapped_column(String(32), nullable=True)

    taxa: Mapped[List["Taxa"]] = relationship(back_populates="inst_taxonomy")


class Taxa(Base):
    """NCBI Taxonomy i.e. species records"""

    __tablename__ = "ncbi_taxa"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)  # NCBI Taxid
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    short_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    taxonomy_id: Mapped[int] = mapped_column(ForeignKey("taxonomy.id"), index=True)

    inst_taxonomy: Mapped["Taxonomy"] = relationship(back_populates="taxa")

    organisms: Mapped[List["Organism"]] = relationship(back_populates="inst_taxa")
    assemblies: Mapped[List["Assembly"]] = relationship(back_populates="inst_taxa")
    annotations: Mapped[List["Annotation"]] = relationship(back_populates="inst_taxa")


class Organism(Base):
    """Organism (cell, tissue, organ) per species (taxa_id)"""

    __tablename__ = "organism"

    id: Mapped[int] = mapped_column(primary_key=True)
    taxa_id: Mapped[int] = mapped_column(ForeignKey("ncbi_taxa.id"), index=True)
    cto: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    __table_args__ = (UniqueConstraint(taxa_id, cto),)

    inst_taxa: Mapped["Taxa"] = relationship(back_populates="organisms")

    selections: Mapped[List["Selection"]] = relationship(back_populates="inst_organism")
    datasets: Mapped[List["Dataset"]] = relationship(back_populates="inst_organism")


class Selection(Base):
    """Association: Modification, Organism, DetectionTechnology.
    This table defines the selections or combinations
    of modification, organism, and technology IDs that are
    actually available in the database, i.e. not all combinations
    of modification, organism, and technology IDs may be
    available."""

    __tablename__ = "selection"

    id: Mapped[int] = mapped_column(primary_key=True)
    modification_id: Mapped[int] = mapped_column(
        ForeignKey("modification.id"), index=True
    )
    organism_id: Mapped[int] = mapped_column(ForeignKey("organism.id"), index=True)
    technology_id: Mapped[int] = mapped_column(ForeignKey("technology.id"), index=True)

    __table_args__ = (
        Index(
            "idx_select", "modification_id", "organism_id", "technology_id", unique=True
        ),
    )

    inst_modification: Mapped["Modification"] = relationship(
        back_populates="selections"
    )
    inst_technology: Mapped["DetectionTechnology"] = relationship(
        back_populates="selections"
    )
    inst_organism: Mapped["Organism"] = relationship(back_populates="selections")


class Assembly(Base):
    """Assembly releases"""

    __tablename__ = "assembly"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    alt_name: Mapped[str] = mapped_column(String(128), nullable=True)
    taxa_id: Mapped[int] = mapped_column(ForeignKey("ncbi_taxa.id"), index=True)
    version: Mapped[str] = mapped_column(
        String(12), nullable=False
    )  # current is assembly_version.version_num

    __table_args__ = (UniqueConstraint(name, taxa_id, version, name="uq_assembly_ntv"),)

    inst_taxa: Mapped["Taxa"] = relationship(back_populates="assemblies")


class AssemblyVersion(Base):
    """Assembly version"""

    __tablename__ = "assembly_version"

    version_num: Mapped[str] = mapped_column(String(12), primary_key=True)


class Annotation(Base):
    """Annotation"""

    __tablename__ = "annotation"

    id: Mapped[int] = mapped_column(primary_key=True)
    release: Mapped[int] = mapped_column(nullable=False)
    taxa_id: Mapped[int] = mapped_column(ForeignKey("ncbi_taxa.id"), index=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(
        String(12), nullable=False
    )  # current is annotation_version.version_num

    __table_args__ = (
        UniqueConstraint(release, taxa_id, source, version, name="uq_annotation_rtv"),
    )

    inst_taxa: Mapped["Taxa"] = relationship(back_populates="annotations")
    annotations: Mapped[List["GenomicAnnotation"]] = relationship(
        back_populates="inst_annotation"
    )


class AnnotationVersion(Base):
    """Annotation version"""

    __tablename__ = "annotation_version"

    version_num: Mapped[str] = mapped_column(String(12), primary_key=True)


class GenomicAnnotation(Base):
    """Gene annotation"""

    __tablename__ = "genomic_annotation"

    id: Mapped[str] = mapped_column(
        String(128), primary_key=True, autoincrement=False
    )  # Ensembl ID or GtRNAdb_id incl. organism
    annotation_id: Mapped[int] = mapped_column(ForeignKey("annotation.id"), index=True)
    name: Mapped[str] = mapped_column(
        String(128), nullable=True
    )  # Ensembl gene name or GtRNAdb_id
    biotype: Mapped[str] = mapped_column(
        String(255), nullable=True
    )  # Ensembl gene biotype or tRNA

    __table_args__ = (Index("idx_genomic", "annotation_id", "biotype", "name"),)

    inst_annotation: Mapped["Annotation"] = relationship(back_populates="annotations")

    annotations: Mapped[List["DataAnnotation"]] = relationship(
        back_populates="inst_genomic"
    )


# for Project and Dataset, allow Optional (None in Python), but nullable=False (NOT NULL)
# to instantiate class, assign later?
class Project(Base):
    """Project metadata"""

    __tablename__ = "project"

    id: Mapped[str] = mapped_column(
        String(8), primary_key=True, autoincrement=False
    )  # SMID
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text)  # TEXT ?
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("project_contact.id"), index=True
    )
    date_published: Mapped[datetime] = mapped_column(
        DateTime, nullable=True
    )  # datetime declaration/default format ?  YYYY-MM-DD ISO 8601
    date_added: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    inst_contact: Mapped["ProjectContact"] = relationship(back_populates="projects")

    sources: Mapped[List["ProjectSource"]] = relationship(back_populates="inst_project")
    datasets: Mapped[List["Dataset"]] = relationship(back_populates="inst_project")


class ProjectContact(Base):
    """Project contact"""

    __tablename__ = "project_contact"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_name: Mapped[str] = mapped_column(String(128), nullable=False)
    contact_institution: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(320), nullable=False)

    projects: Mapped[List["Project"]] = relationship(back_populates="inst_contact")


class ProjectSource(Base):
    """Project external source"""

    __tablename__ = "project_source"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.id"), index=True
    )  # SMID
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pmid: Mapped[Optional[int]] = mapped_column(nullable=True)

    inst_project: Mapped["Project"] = relationship(back_populates="sources")


class Dataset(Base):
    """Dataset metadata"""

    __tablename__ = "dataset"

    id: Mapped[str] = mapped_column(
        String(12), primary_key=True, autoincrement=False
    )  # EUFID
    project_id: Mapped[str] = mapped_column(
        ForeignKey("project.id"), index=True
    )  # SMID
    technology_id: Mapped[int] = mapped_column(ForeignKey("technology.id"), index=True)
    organism_id: Mapped[int] = mapped_column(ForeignKey("organism.id"), index=True)
    date_added: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # bedRMod header
    modification_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # DNA or RNA
    sequencing_platform: Mapped[str] = mapped_column(String(255), nullable=True)
    basecalling: Mapped[str] = mapped_column(Text, nullable=True)
    bioinformatics_workflow: Mapped[str] = mapped_column(Text, nullable=True)
    experiment: Mapped[str] = mapped_column(Text, nullable=True)
    external_source: Mapped[str] = mapped_column(String(255), nullable=True)

    inst_project: Mapped["Project"] = relationship(back_populates="datasets")
    inst_technology: Mapped["DetectionTechnology"] = relationship(
        back_populates="datasets"
    )
    inst_organism: Mapped["Organism"] = relationship(back_populates="datasets")

    associations: Mapped[List["DatasetModificationAssociation"]] = relationship(
        back_populates="inst_dataset"
    )
    datas: Mapped[List["Data"]] = relationship(back_populates="inst_dataset")


class Data(Base):
    """Dataset (records)"""

    __tablename__ = "data"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("dataset.id"), index=True)
    modification_id: Mapped[str] = mapped_column(
        ForeignKey("modification.id"), index=True
    )
    # bedRMod fields - order must match bedRMod columns?
    chrom: Mapped[str] = mapped_column(String(128), nullable=False)
    start: Mapped[int] = mapped_column(nullable=False)
    end: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(ForeignKey("modomics.short_name"))
    score: Mapped[int] = mapped_column(nullable=False, index=True)
    strand: Mapped[Strand] = mapped_column(Enum(Strand), nullable=False)
    thick_start: Mapped[int] = mapped_column(nullable=False)
    thick_end: Mapped[int] = mapped_column(nullable=False)
    item_rgb: Mapped[str] = mapped_column(String(128), nullable=False)
    coverage: Mapped[int] = mapped_column(nullable=False, index=True)
    frequency: Mapped[int] = mapped_column(nullable=False, index=True)

    __table_args__ = (
        Index("idx_data_sort", "chrom", "start", "end"),
        CheckConstraint("start >= 0", name="start"),
        CheckConstraint("start < end", name="start_end"),
        CheckConstraint("thick_start >= 0", name="tstart"),
        CheckConstraint("thick_start < thick_end", name="tstart_end"),
        CheckConstraint("score >= 0", name="score"),
        CheckConstraint("score <= 1000", name="score_max"),
        CheckConstraint("coverage > 0", name="cov_strict"),
        CheckConstraint("frequency > 0", name="freq_strict"),
        CheckConstraint("frequency <= 100", name="freq_max"),
    )

    annotations: Mapped[List["DataAnnotation"]] = relationship(
        back_populates="inst_data"
    )

    inst_dataset: Mapped["Dataset"] = relationship(back_populates="datas")
    inst_modification: Mapped["Modification"] = relationship(back_populates="datas")
    # inst_modomics: Mapped["Modomics"] = relationship(back_populates="datas")


class DatasetModificationAssociation(Base):
    """Association: Dataset, Modification"""

    __tablename__ = "dataset_modification_association"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("dataset.id"), index=True)
    modification_id: Mapped[int] = mapped_column(
        ForeignKey("modification.id"), index=True
    )

    __table_args__ = (Index("idx_assoc", "dataset_id", "modification_id", unique=True),)

    inst_dataset: Mapped["Dataset"] = relationship(back_populates="associations")
    inst_modification: Mapped["Modification"] = relationship(
        back_populates="associations"
    )


class DataAnnotation(Base):
    """Association: GenomicAnnotation, Data"""

    __tablename__ = "data_annotation"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_id: Mapped[int] = mapped_column(ForeignKey("data.id"), index=True)
    gene_id: Mapped[str] = mapped_column(
        ForeignKey("genomic_annotation.id"), index=True
    )
    feature: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # __table_args__ = (Index("idx_data_ann", "data_id", "gene_id"),)
    __table_args__ = (UniqueConstraint(data_id, gene_id, feature),)

    inst_genomic: Mapped["GenomicAnnotation"] = relationship(
        back_populates="annotations"
    )
    inst_data: Mapped["Data"] = relationship(back_populates="annotations")


class Sprinzl(Base):
    """Sprinzl tRNA position numbering"""

    __tablename__ = "sprinzl"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_id: Mapped[int] = mapped_column(ForeignKey("data.id"), index=True)
    position: Mapped[str] = mapped_column(String(32), nullable=False)

    __table_args__ = (UniqueConstraint(data_id, position),)


class UserState(enum.Enum):
    wait_for_confirmation = 0
    active = 1


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, index=True, unique=True
    )
    state: Mapped[UserState] = mapped_column(Enum(UserState), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    confirmation_token: Mapped[str] = mapped_column(String(32), nullable=True)


class BamFile(Base):
    __tablename__ = "bam_file"
    id: Mapped[int] = mapped_column(primary_key=True)
    original_file_name: Mapped[str] = mapped_column(String(1024))
    storage_file_name: Mapped[str] = mapped_column(String(256), unique=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("dataset.id"), index=True)


class UserProjectAssociation(Base):
    __tablename__ = "user_project_association"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id"), index=True)

from scimodom.database.database import Base

from datetime import datetime

from typing import List, Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Modomics(Base):
    """Modified residues"""

    __tablename__ = "modomics"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)  # MODOMICS code
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # NVARCHAR ?
    short_name: Mapped[str] = mapped_column(String(32), nullable=False)  # NVARCHAR ?
    moiety: Mapped[str] = mapped_column(String(32), nullable=False)

    modifications: Mapped[List["Modification"]] = relationship(
        back_populates="inst_modomics"
    )


class Modification(Base):
    """Modification (RNA type)"""

    __tablename__ = "modification"

    id: Mapped[int] = mapped_column(primary_key=True)
    rna: Mapped[str] = mapped_column(String(32), nullable=False)
    modomics_id: Mapped[str] = mapped_column(ForeignKey("modomics.id"))

    inst_modomics: Mapped["Modomics"] = relationship(back_populates="modifications")
    selections: Mapped[List["Selection"]] = relationship(back_populates="modifications")


class DetectionMethod(Base):
    """Detection methods (nomenclature)"""

    __tablename__ = "method"

    id: Mapped[int] = mapped_column(primary_key=True)
    cls: Mapped[str] = mapped_column(String(32), nullable=False)
    meth: Mapped[str] = mapped_column(String(128), nullable=False)

    technologies: Mapped[List["DetectionTechnology"]] = relationship(
        back_populates="inst_method"
    )


class DetectionTechnology(Base):
    """Detection methods (technology)"""

    __tablename__ = "technology"

    id: Mapped[int] = mapped_column(primary_key=True)
    tech: Mapped[str] = mapped_column(String(255), nullable=False)
    method_id: Mapped[int] = mapped_column(ForeignKey("method.id"))

    inst_method: Mapped["DetectionMethod"] = relationship(back_populates="technologies")
    selections: Mapped[List["Selection"]] = relationship(back_populates="technologies")


class Assembly(Base):
    """Assembly"""

    __tablename__ = "assembly"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    taxa_id: Mapped[int] = mapped_column(ForeignKey("ncbi_taxa.id"))
    version: Mapped[str] = mapped_column(
        String(12), nullable=False
    )  # current is assembly_version.version_num

    inst_taxa: Mapped["Taxa"] = relationship(back_populates="assemblies")
    datasets: Mapped[List["Dataset"]] = relationship(back_populates="inst_assembly")


class AssemblyVersion(Base):
    """Assembly version"""

    __tablename__ = "assembly_version"

    version_num: Mapped[str] = mapped_column(String(12), primary_key=True)


class Annotation(Base):
    """Annotation"""

    __tablename__ = "annotation"

    id: Mapped[int] = mapped_column(primary_key=True)
    release: Mapped[int] = mapped_column(nullable=False)
    taxa_id: Mapped[int] = mapped_column(ForeignKey("ncbi_taxa.id"))
    version: Mapped[str] = mapped_column(
        String(12), nullable=False
    )  # current is annotation_version.version_num

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

    id: Mapped[int] = mapped_column(primary_key=True)
    data_id: Mapped[int] = mapped_column(ForeignKey("data.id"))
    annotation_id: Mapped[int] = mapped_column(ForeignKey("annotation.id"))
    feature: Mapped[str] = mapped_column(String(32), nullable=False)
    gene_name: Mapped[str] = mapped_column(String(128), nullable=True)
    gene_id: Mapped[str] = mapped_column(String(128), nullable=True)
    gene_biotype: Mapped[str] = mapped_column(String(255), nullable=True)

    inst_data: Mapped["Data"] = relationship(back_populates="annotations")
    inst_annotation: Mapped["Annotation"] = relationship(back_populates="annotations")


class Taxonomy(Base):
    """Taxonomic rank (up to phylum) for the TreeSelect component"""

    __tablename__ = "taxonomy"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    kingdom: Mapped[str] = mapped_column(String(32), nullable=True)
    phylum: Mapped[str] = mapped_column(String(32), nullable=True)

    taxa: Mapped[List["Taxa"]] = relationship(back_populates="inst_taxonomy")


class Taxa(Base):
    """NCBI Taxonomy"""

    __tablename__ = "ncbi_taxa"

    id: Mapped[int] = mapped_column(primary_key=True)  # NCBI Taxid
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    short_name: Mapped[str] = mapped_column(String(128), nullable=False)
    taxonomy_id: Mapped[int] = mapped_column(ForeignKey("taxonomy.id"))

    assemblies: Mapped[List["Assembly"]] = relationship(back_populates="inst_taxa")
    annotations: Mapped[List["Annotation"]] = relationship(back_populates="inst_taxa")
    inst_taxonomy: Mapped["Taxonomy"] = relationship(back_populates="taxa")
    organisms: Mapped[List["Organism"]] = relationship(back_populates="inst_taxa")
    datasets: Mapped[List["Dataset"]] = relationship(back_populates="inst_taxa")


class Organism(Base):
    """Organism (cell, tissue, organ)"""

    __tablename__ = "organism"

    id: Mapped[int] = mapped_column(primary_key=True)
    cto: Mapped[str] = mapped_column(String(255), nullable=False)
    taxa_id: Mapped[int] = mapped_column(ForeignKey("ncbi_taxa.id"))

    inst_taxa: Mapped["Taxa"] = relationship(back_populates="organisms")
    selections: Mapped[List["Selection"]] = relationship(back_populates="organisms")


class Selection(Base):
    """Association: Modification, DetectionTechnology, Organism"""

    __tablename__ = "selection"

    id: Mapped[int] = mapped_column(primary_key=True)
    modification_id: Mapped[int] = mapped_column(ForeignKey("modification.id"))
    technology_id: Mapped[int] = mapped_column(ForeignKey("technology.id"))
    organism_id: Mapped[int] = mapped_column(ForeignKey("organism.id"))

    __table_args__ = (UniqueConstraint(modification_id, technology_id, organism_id),)

    modifications: Mapped["Modification"] = relationship(back_populates="selections")
    technologies: Mapped["DetectionTechnology"] = relationship(
        back_populates="selections"
    )
    organisms: Mapped["Organism"] = relationship(back_populates="selections")

    associations: Mapped[List["Association"]] = relationship(
        back_populates="selections"
    )


# for Project and Dataset, allow Optional (None in Python), but nullable=False (NOT NULL)
# to instantiate class, assign later?
class Project(Base):
    """Project metadata"""

    __tablename__ = "project"

    id: Mapped[str] = mapped_column(
        String(8), primary_key=True
    )  # SMID - NOT INCREMENT, BUT WHAT?
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text)  # TEXT ?
    contact_id: Mapped[int] = mapped_column(ForeignKey("project_contact.id"))
    date_published: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )  # datetime declaration/default format ?  YYYY-MM-DD ISO 8601
    date_added: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    inst_contact: Mapped["ProjectContact"] = relationship(back_populates="projects")

    sources: Mapped["ProjectSource"] = relationship(back_populates="inst_project")
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
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id"))  # SMID
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # NVARCHAR ?
    pmid: Mapped[Optional[int]] = mapped_column(nullable=True)

    inst_project: Mapped[List["Project"]] = relationship(back_populates="sources")


# bedRMod metadata - redundant taxid, assembly at upload, lifted is None (==assembly) or final assembly
# for RNA type/mod, technology, and tissue/cell/organ, use an association table/model
# allowing, in principle e.g. future change, to have a given bedRMod/dataset to have 1+ RNA type/mod (and technology and/or e.g. cell type)
# although at upload we'd only allow 1+ RNA type/mod
class Dataset(Base):
    """Dataset metadata"""

    __tablename__ = "dataset"

    id: Mapped[str] = mapped_column(String(12), primary_key=True)  # EUFID
    project_id: Mapped[str] = mapped_column(ForeignKey("project.id"))  # SMID
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # header information - bedRMod
    # read from header or selected from dropdown options (SMID/project, RNA type/mod, technology, organism/cto, assembly)
    # we can add a "validator" to check against the file header/records for required fields that are selected at upload
    # e.g. RNA mod, taxid, assembly
    file_format: Mapped[str] = mapped_column(String(32), nullable=False)
    modification_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # DNA or RNA - in principle the latter only...
    taxa_id: Mapped[int] = mapped_column(
        ForeignKey("ncbi_taxa.id")
    )  # redundant - Selection or allow for "double checking"
    assembly_id: Mapped[int] = mapped_column(ForeignKey("assembly.id"))
    # does this work NULL FOREIGN KEY ? or nullable=False, but leave Optional, and fill with assembly i.e. this becomes effectively assembly
    # lifted: Mapped[Optional[int]] = mapped_column(ForeignKey("assembly.id"), nullable=True)
    # in fact, for a given DB version, assembly is fixed, i.e. we know it if we know taxid
    # so keep assembly as the one selected (matched with header), and flag (Boolean) if it was lifted or not
    # when "upgrading" the DB, all data is lifted from old to new assembly, and flag is set to True for all -> dump old DB with stamp
    # so assembly is just really recorded for data tracing
    lifted: Mapped[Optional[bool]] = mapped_column(default=False, nullable=False)
    annotation_source: Mapped[str] = mapped_column(String(128), nullable=False)
    annotation_version: Mapped[str] = mapped_column(
        String(128), nullable=False
    )  # VARCHAR or INTEGER - can we fix this at upload ?
    # all optional - from header only
    sequencing_platform: Mapped[str] = mapped_column(String(255), nullable=True)
    basecalling: Mapped[str] = mapped_column(Text, nullable=True)
    bioinformatics_workflow: Mapped[str] = mapped_column(Text, nullable=True)
    experiment: Mapped[str] = mapped_column(Text, nullable=True)
    external_source: Mapped[str] = mapped_column(String(255), nullable=True)

    inst_project: Mapped["Project"] = relationship(back_populates="datasets")
    inst_assembly: Mapped["Assembly"] = relationship(back_populates="datasets")
    inst_taxa: Mapped["Taxa"] = relationship(back_populates="datasets")

    associations: Mapped[List["Association"]] = relationship(back_populates="datasets")
    records: Mapped[List["Data"]] = relationship(back_populates="inst_dataset")


class Association(Base):
    """Association: Dataset, Selection"""

    __tablename__ = "association"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("dataset.id"))
    selection_id: Mapped[int] = mapped_column(ForeignKey("selection.id"))

    __table_args__ = (UniqueConstraint(dataset_id, selection_id),)

    datasets: Mapped["Dataset"] = relationship(back_populates="associations")
    selections: Mapped["Selection"] = relationship(back_populates="associations")


class Data(Base):
    """Dataset (records)"""

    __tablename__ = "data"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("dataset.id"))  # EUFID
    # bedRMod fields - order must match bedRMod columns?
    chrom: Mapped[str] = mapped_column(String(128), nullable=False)
    start: Mapped[int] = mapped_column(nullable=False)
    end: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(32), nullable=False)  # as is ?
    score: Mapped[int] = mapped_column(nullable=False)
    strand: Mapped[str] = mapped_column(String(1), nullable=False)
    thick_start: Mapped[int] = mapped_column(nullable=False)
    thick_end: Mapped[int] = mapped_column(nullable=False)
    item_rgb: Mapped[str] = mapped_column(String(128), nullable=False)
    coverage: Mapped[int] = mapped_column(nullable=False)
    frequency: Mapped[int] = mapped_column(nullable=False)
    ref_base: Mapped[str] = mapped_column(String(1), nullable=False)

    inst_dataset: Mapped["Dataset"] = relationship(back_populates="records")
    annotations: Mapped[List["GenomicAnnotation"]] = relationship(
        back_populates="inst_data"
    )

from functools import cache
from itertools import chain
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    DetectionMethod,
    DetectionTechnology,
    Modification,
    Modomics,
    Organism,
    RNAType,
    Taxonomy,
    Taxa,
    Selection,
)
from scimodom.services.annotation.generic import GenericAnnotationService
from scimodom.services.assembly import get_assembly_service, AssemblyService
import scimodom.utils.specifications as specs


class UtilitiesService:
    """Collection of common requests that are
    used to run the application."""

    def __init__(self, session: Session, assembly_service: AssemblyService):
        self._session = session
        self._assembly_service = assembly_service

    def get_rna_types(self) -> list[dict[str, Any]]:
        """Get all RA types.

        :returns: Selected columns from RNAType
        :rtype: list of dict
        """
        rna_types = self._session.scalars(select(RNAType)).all()
        return [{"id": rna.id, "label": rna.name} for rna in rna_types]

    def get_taxa(self) -> list[dict[str, Any]]:
        """Get all organisms with their taxonomy.

        :returns: Selected columns from Taxa and Taxonomy
        :rtype: list of dict
        """
        rows = self._session.execute(
            select(Taxa, Taxonomy).join(Taxonomy, Taxa.inst_taxonomy)
        )
        return [
            {
                "id": row.Taxa.id,
                "taxa_sname": row.Taxa.short_name,
                "domain": row.Taxonomy.domain,
                "kingdom": row.Taxonomy.kingdom,
                "phylum": row.Taxonomy.phylum,
            }
            for row in rows
        ]

    def get_modomics(self) -> list[dict[str, Any]]:
        """Get all modifications.

        :returns: Selected columns from Modomics
        :rtype: list of dict
        """
        modomics = self._session.scalars(select(Modomics)).all()
        return [{"id": mod.id, "modomics_sname": mod.short_name} for mod in modomics]

    def get_methods(self) -> list[dict[str, Any]]:
        """Get all standard methods.

        :returns: Selected columns from DetectionMethod
        :rtype: list of dict
        """
        methods = self._session.scalars(select(DetectionMethod)).all()
        return [
            {"id": method.id, "cls": method.cls, "meth": method.meth}
            for method in methods
        ]

    def get_selections(self) -> list[dict[str, Any]]:
        """Get available selections.

        :returns: Selected columns from ORM models
        for available selections.
        :rtype: list of dict
        """
        query = (
            select(
                Modification.id.label("modification_id"),
                Modification.rna,
                Modomics.short_name.label("modomics_sname"),
                DetectionTechnology.id.label("technology_id"),
                DetectionMethod.cls,
                DetectionMethod.meth,
                DetectionTechnology.tech,
                Organism.id.label("organism_id"),
                Taxonomy.domain,
                Taxonomy.kingdom,
                Taxa.id.label("taxa_id"),
                Taxa.short_name.label("taxa_sname"),
                Organism.cto,
                Selection.id.label("selection_id"),
            )
            .join_from(
                Selection,
                Modification,
                Selection.inst_modification,
            )
            .join_from(
                Selection,
                DetectionTechnology,
                Selection.inst_technology,
            )
            .join_from(Selection, Organism, Selection.inst_organism)
            .join_from(Modification, Modomics, Modification.inst_modomics)
            .join_from(
                DetectionTechnology,
                DetectionMethod,
                DetectionTechnology.inst_method,
            )
            .join_from(Organism, Taxa, Organism.inst_taxa)
            .join_from(Taxa, Taxonomy, Taxa.inst_taxonomy)
        )
        return [row._asdict() for row in self._session.execute(query)]

    def get_genes(self, selection_ids: list[int]) -> list[str]:
        """Retrieve gene list for selection.

        :param selection_ids: Selection ID(s)
        :type selection_ids: list of int
        :returns: Combined list of genes
        :rtype: list of str
        """
        cache_path = GenericAnnotationService.get_cache_path()
        files = [Path(cache_path, str(selection_id)) for selection_id in selection_ids]
        genes = [fc.read_text().split() for fc in files]
        return list(set(chain(*genes)))

    # this now depends on RNA type WTS or tRNA...
    def get_annotation(self, rna_type: str):
        response = dict()
        response["features"] = ["Exonic", "Intronic"]  # self.FEATURES
        response["biotypes"] = ["tmp"]  # self.MAPPED_BIOTYPES
        return response

    # this now depends on RNA type WTS or tRNA..
    # FEATURES: ClassVar[list[str]] = sorted(
    #     list(
    #         {
    #             **AnnotationService.FEATURES["conventional"],
    #             **AnnotationService.FEATURES["extended"],
    #         }.values()
    #     )
    # )
    # BIOTYPES: ClassVar[dict[str, str]] = specs.BIOTYPES
    # MAPPED_BIOTYPES: ClassVar[list[str]] = sorted(list(set(BIOTYPES.values())))

    def get_chroms(self, taxa_id) -> list[dict[str, Any]]:
        """Provides access to chrom.sizes for a given
        organism for the latest database version.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: chrom names and sizes
        :rtype: list of dict
        """
        chroms = []
        chrom_file = self._assembly_service.get_chrom_file(taxa_id)
        with open(chrom_file, "r") as fh:
            for line in fh:
                chrom, size = line.strip().split(None, 1)
                chroms.append({"chrom": chrom, "size": int(size.strip())})
        return chroms

    def get_assemblies(self, taxa_id: int) -> list[dict[str, Any]]:
        """Get available assemblies for given organism.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: Selected columns from Assembly
        :rtype: list of dict
        """
        assemblies = self._assembly_service.get_assemblies_by_taxa(taxa_id)
        return [{"id": assembly.id, "name": assembly.name} for assembly in assemblies]

    def _dump(self, query):
        """Serialize a query from a select statement using
        individual columns of an ORM entity, i.e. using execute(),
        the statement must return rows that have individual elements
        per value, each corresponding to a separate column.

        :param query: SQLAlchemy statement
        :type query: SQLAlchemy Select object
        :returns: Query result
        :rtype: list of dict
        """
        return [r._asdict() for r in self._session.execute(query)]


@cache
def get_utilities_service() -> UtilitiesService:
    """Instantiates a UtilitiesService object.

    :returns: UtilitiesService instance
    :rtype: UtilitiesService
    """
    return UtilitiesService(
        session=get_session(), assembly_service=get_assembly_service()
    )

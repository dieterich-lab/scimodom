from functools import cache
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Data,
    Dataset,
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
from scimodom.services.assembly import get_assembly_service, AssemblyService


class UtilitiesService:
    """Collection of common requests that are
    used to run the application."""

    def __init__(
        self,
        session: Session,
        assembly_service: AssemblyService,
    ) -> None:
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
                RNAType.name.label("rna_name"),
                Modomics.short_name.label("modomics_sname"),
                DetectionTechnology.id.label("technology_id"),
                DetectionMethod.cls,
                DetectionMethod.meth,
                DetectionTechnology.tech,
                Organism.id.label("organism_id"),
                Taxonomy.domain,
                Taxonomy.kingdom,
                Taxa.id.label("taxa_id"),
                Taxa.name.label("taxa_name"),
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
            .join_from(Modification, RNAType, Modification.inst_rna)
            .join_from(
                DetectionTechnology,
                DetectionMethod,
                DetectionTechnology.inst_method,
            )
            .join_from(Organism, Taxa, Organism.inst_taxa)
            .join_from(Taxa, Taxonomy, Taxa.inst_taxonomy)
        )
        return [row._asdict() for row in self._session.execute(query)]

    def get_assemblies(self, taxa_id: int) -> list[dict[str, Any]]:
        """Get available assemblies for given organism.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: Selected columns from Assembly
        :rtype: list of dict
        """
        assemblies = self._assembly_service.get_assemblies_by_taxa(taxa_id)
        return [{"id": assembly.id, "name": assembly.name} for assembly in assemblies]

    def get_release_info(self):
        query = select(Data)
        sites = self._session.scalar(
            select(func.count()).select_from(query.with_only_columns(Data.id))
        )
        datasets = self._session.scalar(
            select(func.count()).select_from(query.with_only_columns(Dataset.id))
        )
        return {"sites": sites, "datasets": datasets}

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
        session=get_session(),
        assembly_service=get_assembly_service(),
    )

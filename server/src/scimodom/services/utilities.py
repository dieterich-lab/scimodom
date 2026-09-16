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
from scimodom.services.annotation import BIOTYPES


MAPPED_BIOTYPES = sorted(set(BIOTYPES.values()))


class UtilitiesService:
    """Provide a collection of general queries."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    @staticmethod
    def get_biotypes() -> dict[str, list[str]]:
        """Get all biotypes.

        NOTE: biotypes are independent of species/RNA type.
        To evaluate dynamically, remove module-level constant,
        and use here mapped_biotypes = sorted(set(BIOTYPES.values()))

        :return: Biotypes values used in the UI
        """
        return {"biotypes": MAPPED_BIOTYPES}

    def get_rna_types(self) -> list[dict[str, Any]]:
        """Get all RNA types.

        :return: Identifier and label from RNAType
        """
        rna_types = self._session.scalars(select(RNAType)).all()
        return [{"id": rna.id, "label": rna.name} for rna in rna_types]

    def get_taxa(self) -> list[dict[str, Any]]:
        """Get all species with their taxonomy.

        :return: Identifier, name and short name from Taxa; domain,
        kingdom, and phylum from Taxonomy.
        """
        rows = self._session.execute(
            select(Taxa, Taxonomy).join(Taxonomy, Taxa.inst_taxonomy)
        )
        return [
            {
                "taxa_id": row.Taxa.id,
                "taxa_name": row.Taxa.name,
                "taxa_sname": row.Taxa.short_name,
                "domain": row.Taxonomy.domain,
                "kingdom": row.Taxonomy.kingdom,
                "phylum": row.Taxonomy.phylum,
            }
            for row in rows
        ]

    def get_modomics(self) -> list[dict[str, Any]]:
        """Get all modifications.

        :return: Identifier (MODOMICS code) and short name from Modomics
        """
        modomics = self._session.scalars(select(Modomics)).all()
        return [{"id": mod.id, "modomics_sname": mod.short_name} for mod in modomics]

    def get_methods(self) -> list[dict[str, Any]]:
        """Get all detection methods.

        :return: Identifier, class, and method from DetectionMethod
        """
        methods = self._session.scalars(select(DetectionMethod)).all()
        return [
            {"id": method.id, "cls": method.cls, "meth": method.meth}
            for method in methods
        ]

    def get_selections(self) -> list[dict[str, Any]]:
        """Get all selections.

        Selections are defined by an association:
        Modification, Organism, DetectionTechnology.

        :return: Selected columns from various ORM models
        describing each selection in detail.
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

    def get_release_info(self) -> dict[str, int]:
        """Get number of sites and datasets for current release.

        :return: Number of sites and datasets
        """
        query = select(Data)
        sites = self._session.scalar(
            select(func.count()).select_from(
                query.with_only_columns(Data.id).subquery()
            )
        )
        datasets = self._session.scalar(
            select(func.count()).select_from(
                query.with_only_columns(Dataset.id).subquery()
            )
        )
        return {"sites": sites, "datasets": datasets}


@cache
def get_utilities_service() -> UtilitiesService:
    """Instantiate a UtilitiesService object.

    :return: UtilitiesService instance
    """
    return UtilitiesService(
        session=get_session(),
    )

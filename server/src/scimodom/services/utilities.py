from collections import defaultdict
from functools import cache
from typing import ClassVar, Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Data,
    Dataset,
    DatasetModificationAssociation,
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
from scimodom.services.annotation import (
    get_annotation_service,
    AnnotationService,
)
from scimodom.services.assembly import get_assembly_service, AssemblyService
from scimodom.services.file import FileService, get_file_service
from scimodom.utils.specifications import BIOTYPES


class UtilitiesService:
    """Collection of common requests that are
    used to run the application."""

    def __init__(
        self,
        session: Session,
        assembly_service: AssemblyService,
        annotation_service: AnnotationService,
        file_service: FileService,
    ) -> None:
        self._session = session
        self._assembly_service = assembly_service
        self._annotation_service = annotation_service
        self._file_service = file_service

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

    def get_chart_data(self, chart: str) -> list[dict[str, Any]]:
        """Retrieve the count of data records stratified
        by modification, organism, and technology.

        :param chart: Chart type: Search or Browse
        :type chart: str
        :returns: JSON-like description of database content
        for data records
        :rtype: dict[str, Any]
        """
        query = select(
            Modomics.short_name.label("modification_name"),
            Taxa.short_name.label("species_name"),
            Organism.cto.label("organism_name"),
            DetectionTechnology.tech.label("technology_name"),
            func.count().label("technology_count"),
        )
        if chart == "search":
            query = (
                query.select_from(Data)
                .join(Modification, Data.modification_id == Modification.id)
                .join(Modomics, Modification.modomics_id == Modomics.id)
                .join(Dataset, Data.dataset_id == Dataset.id)
                .join(Organism, Dataset.organism_id == Organism.id)
                .join(Taxa, Organism.taxa_id == Taxa.id)
                .join(
                    DetectionTechnology, Dataset.technology_id == DetectionTechnology.id
                )
            )
        else:
            query = (
                query.select_from(Dataset)
                .join(
                    DatasetModificationAssociation,
                    Dataset.id == DatasetModificationAssociation.dataset_id,
                )
                .join(
                    Modification,
                    DatasetModificationAssociation.modification_id == Modification.id,
                )
                .join(Modomics, Modification.modomics_id == Modomics.id)
                .join(Organism, Dataset.organism_id == Organism.id)
                .join(Taxa, Organism.taxa_id == Taxa.id)
                .join(
                    DetectionTechnology, Dataset.technology_id == DetectionTechnology.id
                )
            )

        query = query.group_by(
            Modomics.short_name, Taxa.short_name, Organism.cto, DetectionTechnology.tech
        )
        result = self._session.execute(query).fetchall()

        structure = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        )
        for mod_name, species_name, org_name, tech_name, count in result:
            structure[mod_name][species_name][org_name][tech_name] = count

        json_data = [
            {
                "name": chart.capitalize(),
                "children": [
                    {
                        "name": mod,
                        "children": [
                            {
                                "name": species,
                                "children": [
                                    {
                                        "name": org,
                                        "children": [
                                            {"name": tech, "size": size}
                                            for tech, size in techs.items()
                                        ],
                                    }
                                    for org, techs in orgs.items()
                                ],
                            }
                            for species, orgs in species_data.items()
                        ],
                    }
                    for mod, species_data in structure.items()
                ],
            }
        ]
        return json_data

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
        annotation_service=get_annotation_service(),
        file_service=get_file_service(),
    )

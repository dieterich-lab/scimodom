from functools import cache
from itertools import chain
from pathlib import Path
from typing import ClassVar, Optional


from sqlalchemy import select, func
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Annotation,
    Assembly,
    Data,
    DataAnnotation,
    Dataset,
    DetectionMethod,
    DetectionTechnology,
    GenomicAnnotation,
    Modification,
    Modomics,
    Organism,
    Project,
    ProjectContact,
    ProjectSource,
    RNAType,
    Taxonomy,
    Taxa,
    Selection,
)
import scimodom.database.queries as queries
from scimodom.services.annotation import AnnotationService
from scimodom.services.assembly import get_assembly_service
import scimodom.utils.specifications as specs


class UtilitiesService:
    """Collection of common requests that are
    used to run the application."""

    # this now depends on RNA type WTS or tRNA..
    # FEATURES: ClassVar[list[str]] = sorted(
    #     list(
    #         {
    #             **AnnotationService.FEATURES["conventional"],
    #             **AnnotationService.FEATURES["extended"],
    #         }.values()
    #     )
    # )
    BIOTYPES: ClassVar[dict[str, str]] = specs.BIOTYPES
    MAPPED_BIOTYPES: ClassVar[list[str]] = sorted(list(set(BIOTYPES.values())))

    def __init__(self, session: Session):
        self._session = session

    def get_gene_list(self, selection_ids):
        """Retrieve gene list for selection.

        :param selection_ids: Selection ID(s)
        :type selection_ids: list of int
        :returns: Query result
        :rtype: list
        """
        # cache_path = AnnotationService.get_cache_path()
        # files = [Path(cache_path, str(selection_id)) for selection_id in selection_ids]
        # genes = [fc.read_text().split() for fc in files]
        # return list(set(chain(*genes)))
        return ["A", "B"]

    # this now depends on RNA type WTS or tRNA...
    def get_features_and_biotypes(self):
        response = dict()
        response["features"] = ["Exonic", "Intronic"]  # self.FEATURES
        response["biotypes"] = self.MAPPED_BIOTYPES
        return response

    def get_rna_types(self):
        """Get all RA types.

        :returns: Query result
        :rtype: list of dict
        """

        query = select(RNAType.id, RNAType.name.label("label"))
        return self._dump(query)

    def get_modomics(self):
        """Get all modifications.

        :returns: Query result
        :rtype: list of dict
        """

        query = select(Modomics.id, Modomics.short_name.label("modomics_sname"))
        return self._dump(query)

    def get_detection_method(self):
        """Get all standard methods.

        :returns: Query result
        :rtype: list of dict
        """

        query = select(DetectionMethod.id, DetectionMethod.cls, DetectionMethod.meth)
        return self._dump(query)

    def get_taxa(self):
        """Get all organisms with their taxonomy.

        :returns: Query result
        :rtype: list of dict
        """

        query = select(
            Taxa.id,
            Taxa.short_name.label("taxa_sname"),
            Taxonomy.domain,
            Taxonomy.kingdom,
            Taxonomy.phylum,
        ).join_from(Taxa, Taxonomy, Taxa.inst_taxonomy)

        return self._dump(query)

    def get_assembly_for_taxid(self, taxid: int):
        """Get available assemblies for given Taxa ID.

        :param taxid: Taxa ID
        :type taxid: int
        :returns: Query result
        :rtype: list of dict
        """

        query = select(Assembly.id, Assembly.name).where(Assembly.taxa_id == taxid)
        return self._dump(query)

    def get_selection(self):
        """Get available selections.

        :returns: Query result
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

        return self._dump(query)

    def get_chrom(self, taxa_id) -> list[dict[str, str | int]]:
        """Provides access to chrom.sizes for one
        selected organism for current database version.

        :param taxid: Taxa ID
        :type taxid: int
        :returns: chrom names and sizes
        :rtype: list of dict
        """
        assembly_service = get_assembly_service()
        chrom_file = assembly_service.get_chrom_file(taxa_id)

        chroms = []
        with open(chrom_file, "r") as fh:
            for line in fh:
                chrom, size = line.strip().split(None, 1)
                chroms.append({"chrom": chrom, "size": int(size.strip())})

        return chroms

    def _get_annotation_id(self, taxid: int) -> int:
        version_query = queries.get_annotation_version()
        version = self._session.execute(version_query).scalar_one()
        query = queries.query_column_where(
            Annotation,
            "id",
            filters={"taxa_id": taxid, "version": version},
        )
        return self._session.execute(query).scalar_one()

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
    return UtilitiesService(session=get_session())

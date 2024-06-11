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
from scimodom.services.assembly import AssemblyService
import scimodom.utils.specifications as specs


class PublicService:
    """Utility class to handle all public requests.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param FEATURES: List of features
    :type FEATURES: list of str
    :param BIOTYPES: Available biotypes
    :type BIOTYPES: dict of {str, str}
    :param MAPPED_BIOTYPES: List of biotypes to use
    :type MAPPED_BIOTYPES: list of str
    """

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
        cache_path = AnnotationService.get_cache_path()
        files = [Path(cache_path, str(selection_id)) for selection_id in selection_ids]
        genes = [fc.read_text().split() for fc in files]
        return list(set(chain(*genes)))

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

    def get_chrom(self, taxid) -> list[dict[str, str | int]]:
        """Provides access to chrom.sizes for one
        selected organism for current database version.

        :param taxid: Taxa ID
        :type taxid: int
        :returns: chrom names and sizes
        :rtype: list of dict
        """
        query = queries.get_assembly_version()
        version = self._session.execute(query).scalar_one()
        query = queries.query_column_where(
            Assembly, ["name", "id"], filters={"taxa_id": taxid, "version": version}
        )
        assembly_name, assembly_id = self._session.execute(query).all()[0]
        query = queries.query_column_where(Taxa, "name", filters={"id": taxid})
        organism_name = self._session.execute(query).scalar_one()
        assembly_service = AssemblyService.from_id(
            self._session, assembly_id=assembly_id
        )
        parent, filen = assembly_service.get_chrom_path(organism_name, assembly_name)
        chrom_file = Path(parent, filen)

        chroms = []
        with open(chrom_file, "r") as fh:
            for line in fh:
                chrom, size = line.strip().split(None, 1)
                chroms.append({"chrom": chrom, "size": int(size.strip())})

        return chroms

    def get_search(
        self,
        modification_id: int,
        organism_id: int,
        technology_ids: list[int],
        taxa_id: int,
        gene_filter: list[str],
        chrom: str | None,
        chrom_start: int,
        chrom_end: int,
        first_record: int,
        max_records: int,
        multi_sort: list[str],
    ):
        """Get Data records for conditional selection, add
        filters and sort.

        Note: For Search, modification ID is unique, but
        more than one technology IDs are allowed.

        :param selection_ids: Selection IDs
        :type selection_ids: list of int
        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param gene_filter: Filters (gene-related)
        :type gene_filter: list of str
        :param chrom: Chromosome
        :type chrom: str
        :param chrom_start: Chromosome start
        :type chrom_start: int
        :param chrom_end: Chromosome end
        :type chrom_end: int
        :param first_record: First record
        :type first_record: int
        :param max_records: Number of records
        :type max_records: int
        :param multi_sort: Sorting criteria
        :type multi_sort: list of str
        :returns: Query results
        :rtype: list of dict
        """

        def _get_arg_sort(string: str, url_split: str = "%2B") -> str:
            """Format Data table sort.

            :param string: Formatted sort string
            :type string: str
            :param url_split: Separator
            :type url_split: str
            :returns: Query string
            :rtype: str
            """
            col, order = string.split(url_split)
            return f"Data.{col}.{order}()"

        def _get_flt(string, url_split="%2B") -> tuple[str, list[str], str]:
            """Retrieve generic filters. The operator
            can be used as a key, and may not
            necessarily match an SQLAlchemy operator.

            :param string: Formatted filter string
            :type string: str
            :param url_split: Separator
            :type url_split: str
            :returns: Tuple of (column, list of values, operator)
            :rtype: tuple
            """
            col, val, operator = string.split(url_split)
            return col, val.split(","), operator

        query = (
            select(
                Data.id,
                Data.chrom,
                Data.start,
                Data.end,
                Data.name,
                Data.score,
                Data.strand,
                Data.coverage,
                Data.frequency,
                Data.dataset_id,
                func.group_concat(DataAnnotation.feature.distinct()).label("feature"),
                func.group_concat(GenomicAnnotation.biotype.distinct()).label(
                    "gene_biotype"
                ),
                func.group_concat(GenomicAnnotation.name.distinct()).label("gene_name"),
                DetectionTechnology.tech,
                Organism.taxa_id,
                Organism.cto,
            )
            .join_from(DataAnnotation, Data, DataAnnotation.inst_data)
            .join_from(DataAnnotation, GenomicAnnotation, DataAnnotation.inst_genomic)
            .join_from(Data, Dataset, Data.inst_dataset)
            .join_from(Dataset, DetectionTechnology, Dataset.inst_technology)
            .join_from(Dataset, Organism, Dataset.inst_organism)
            .where(
                Data.modification_id == modification_id,
                Dataset.organism_id == organism_id,
                Dataset.technology_id.in_(technology_ids),
            )
        )

        # coordinate filters
        if chrom:
            query = (
                query.where(Data.chrom == chrom)
                .where(Data.start >= chrom_start)
                .where(Data.end <= chrom_end)
            )

        # gene filters: matchMode unused (cf. PrimeVue), but keep it this way
        # e.g. to extend options or add table filters
        # gene name
        name_flt = next((flt for flt in gene_filter if "gene_name" in flt), None)
        if name_flt:
            _, name, _ = _get_flt(name_flt)
            query = query.where(GenomicAnnotation.name == name[0])
        # annotation filter
        feature_flt = next((flt for flt in gene_filter if "feature" in flt), None)
        if feature_flt:
            _, features, _ = _get_flt(feature_flt)
            query = query.where(DataAnnotation.feature.in_(features))
        # biotypes
        # index speed up on annotation_id + biotypes + name
        biotype_flt = next((flt for flt in gene_filter if "gene_biotype" in flt), None)
        if biotype_flt:
            annotation_id = self._get_annotation_id(taxa_id)
            _, mapped_biotypes, _ = _get_flt(biotype_flt)
            biotypes = [k for k, v in self.BIOTYPES.items() if v in mapped_biotypes]
            query = query.where(GenomicAnnotation.annotation_id == annotation_id).where(
                GenomicAnnotation.biotype.in_(biotypes)
            )

        query = query.group_by(DataAnnotation.data_id)

        # get length
        length = self._session.scalar(
            select(func.count()).select_from(query.with_only_columns(Data.id))
        )

        # sort filters
        # index speed up for chrom + start
        if not multi_sort:
            chrom_expr = _get_arg_sort("chrom%2Basc")
            start_expr = _get_arg_sort("start%2Basc")
            query = query.order_by(eval(chrom_expr), eval(start_expr))
        else:
            for flt in multi_sort:
                expr = _get_arg_sort(flt)
                query = query.order_by(eval(expr))

        # paginate
        query = query.offset(first_record).limit(max_records)

        response = dict()
        response["totalRecords"] = length
        response["records"] = self._dump(query)

        return response

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


_cached_public_service: Optional[PublicService] = None


def get_public_service() -> PublicService:
    """Instantiates a PublicService object.

    :returns: PublicService instance
    :rtype: PublicService
    """
    global _cached_public_service
    if _cached_public_service is None:
        _cached_public_service = PublicService(session=get_session())
    return _cached_public_service

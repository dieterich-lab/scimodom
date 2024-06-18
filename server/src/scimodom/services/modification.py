from functools import cache

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Data,
    DataAnnotation,
    Dataset,
    DetectionMethod,
    DetectionTechnology,
    GenomicAnnotation,
    Organism,
)


class ModificationService:
    def __init__(self, session: Session):
        self._db_session = session

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


@cache
def get_modification_service() -> ModificationService:
    """Instantiates a ModificationService object.

    :returns: ModificationService instance
    :rtype: ModificationService
    """
    return ModificationService(session=get_session())

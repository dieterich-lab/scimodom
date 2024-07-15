from functools import cache

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Data,
    Annotation,
    DataAnnotation,
    Dataset,
    DetectionMethod,
    DetectionTechnology,
    GenomicAnnotation,
    Modification,
    Modomics,
    Organism,
)
from scimodom.services.annotation import (
    get_annotation_service,
    AnnotationService,
    AnnotationSource,
)
from scimodom.utils.specifications import BIOTYPES


class ModificationService:
    def __init__(self, session: Session, annotation_service: AnnotationService) -> None:
        self._session = session
        self._annotation_service = annotation_service

    def get_modifications_by_source(
        self,
        annotation_source: AnnotationSource,
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

        # TODO: so far annotation_service is only needed to get the id from taxa_id
        # so maybe we can just query it using taxa_id and annotation_source...
        # and if we switch by source before anyway, we can simplify this
        # TODO : biotypes?
        annotation = self._annotation_service.get_annotation(annotation_source, taxa_id)

        if annotation_source == AnnotationSource.ENSEMBL:
            query, length = self._return_ensembl_query(
                annotation,
                modification_id,
                organism_id,
                technology_ids,
                taxa_id,
                gene_filter,
                chrom,
                chrom_start,
                chrom_end,
                first_record,
                max_records,
                multi_sort,
            )
        elif annotation_source == AnnotationSource.GTRNADB:
            pass  # raise not implemented
        else:
            pass  # raise not implemented

        return {
            "totalRecords": length,
            "records": [row._asdict() for row in self._session.execute(query)],
        }

    def _return_ensembl_query(
        self,
        annotation: Annotation,
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
            _, name, _ = self._get_flt(name_flt)
            query = query.where(GenomicAnnotation.name == name[0])
        # annotation filter
        feature_flt = next((flt for flt in gene_filter if "feature" in flt), None)
        if feature_flt:
            _, features, _ = self._get_flt(feature_flt)
            query = query.where(DataAnnotation.feature.in_(features))
        # biotypes
        # index speed up on annotation_id + biotypes + name
        biotype_flt = next((flt for flt in gene_filter if "gene_biotype" in flt), None)
        if biotype_flt:
            _, mapped_biotypes, _ = self._get_flt(biotype_flt)
            biotypes = [k for k, v in BIOTYPES.items() if v in mapped_biotypes]
            query = query.where(GenomicAnnotation.annotation_id == annotation.id).where(
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
            chrom_expr = self._get_arg_sort("chrom%2Basc")
            start_expr = self._get_arg_sort("start%2Basc")
            query = query.order_by(eval(chrom_expr), eval(start_expr))
        else:
            for flt in multi_sort:
                expr = self._get_arg_sort(flt)
                query = query.order_by(eval(expr))

        # paginate
        query = query.offset(first_record).limit(max_records)

        # query = query.add_columns(Modomics.reference_id).join_from(Data, Modification, Data.inst_modification).join_from(Modification, Modomics, Modification.inst_modomics)
        query = query.add_columns(Modomics.reference_id).join_from(
            Data, Modomics, Data.name == Modomics.short_name
        )

        return query, length

    @staticmethod
    def _get_arg_sort(string: str, url_split: str = "%2B") -> str:
        col, order = string.split(url_split)
        return f"Data.{col}.{order}()"

    @staticmethod
    def _get_flt(string, url_split="%2B") -> tuple[str, list[str], str]:
        col, val, operator = string.split(url_split)
        return col, val.split(","), operator


@cache
def get_modification_service() -> ModificationService:
    """Instantiates a ModificationService object.

    :returns: ModificationService instance
    :rtype: ModificationService
    """
    return ModificationService(
        session=get_session(), annotation_service=get_annotation_service()
    )

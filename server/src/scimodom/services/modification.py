from functools import cache
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Data,
    Annotation,
    DataAnnotation,
    Dataset,
    DetectionTechnology,
    GenomicAnnotation,
    Modification,
    Modomics,
    Organism,
    Taxa,
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

    # TODO: annotation_source, cf. #97
    def get_modifications_by_source(
        self,
        annotation_source: AnnotationSource,
        modification_id: int,
        organism_id: int,
        technology_ids: list[int],
        taxa_id: int,
        gene_filter: list[str],
        chrom: str | None,
        chrom_start: int | None,
        chrom_end: int | None,
        first_record: int | None,
        max_records: int | None,
        multi_sort: list[str],
    ) -> dict[str, Any]:
        """Get Data records for conditional selection, add
        filters and sort.

        Note: For Search, modification ID is unique, but
        more than one technology IDs are allowed.

        :param annotation_source: Source of annotation
        :type annotation_source: AnnotationSource
        :param modification_id: Modification ID
        :type modification_id: int
        :param organism_id: Organism ID
        :type organism_id: int
        :param technology_ids: Technology IDs
        :type technology_ids: list[int]
        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param gene_filter: Filters (gene-related)
        :type gene_filter: list of str
        :param chrom: Chromosome
        :type chrom: str
        :param chrom_start: Chromosome start
        :type chrom_start: int | None
        :param chrom_end: Chromosome end
        :type chrom_end: int | None
        :param first_record: first record
        :type first_record: int | None
        :param max_records: number of records
        :type max_records: int | None
        :param multi_sort: sorting criteria
        :type multi_sort: list of str
        :returns: query results
        :rtype: dict[str, Any]
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

    def get_modification_by_gene(
        self,
        annotation_source: AnnotationSource,
        taxa_id: int,
        gene_filter: list[str],
        chrom: str | None,
        chrom_start: int | None,
        chrom_end: int | None,
        first_record: int | None,
        max_records: int | None,
        multi_sort: list[str],
    ) -> dict[str, Any]:
        """Get Data records when searching by gene, add
        filters and sort.

        :param annotation_source: Source of annotation
        :type annotation_source: AnnotationSource
        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param gene_filter: Filters (gene-related)
        :type gene_filter: list of str
        :param chrom: Chromosome
        :type chrom: str
        :param chrom_start: Chromosome start
        :type chrom_start: int | None
        :param chrom_end: Chromosome end
        :type chrom_end: int | None
        :param first_record: first record
        :type first_record: int | None
        :param max_records: number of records
        :type max_records: int | None
        :param multi_sort: sorting criteria
        :type multi_sort: list of str
        :returns: query results
        :rtype: dict[str, Any]
        """

        # TODO: see above
        annotation = self._annotation_service.get_annotation(annotation_source, taxa_id)
        # TODO: currently ignore annotation_source
        if annotation_source == AnnotationSource.ENSEMBL:
            query, length = self._return_gene_query(
                annotation,
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

    def get_modification_site(
        self,
        chrom: str,
        start: int,
        end: int,
    ):
        """Retrieve information related to a modification site.

        :param chrom: Chromosome
        :type chrom: str
        :param chrom_start: Chromosome start
        :type chrom_start: int
        :param chrom_end: Chromosome end
        :type chrom_end: int
        :returns: query results
        :rtype: list of dict
        """
        query = (
            select(
                Data.dataset_id,
                Data.modification_id,
                Modification.rna,
                Data.name,
                Taxa.short_name,
                Organism.cto,
                DetectionTechnology.tech,
                Data.chrom,
                Data.start,
                Data.end,
                Data.strand,
                Data.score,
                Data.coverage,
                Data.frequency,
            )
            .join_from(Data, Dataset, Data.inst_dataset)
            .join_from(Data, Modification, Data.inst_modification)
            .join_from(Dataset, Organism, Dataset.inst_organism)
            .join_from(Dataset, DetectionTechnology, Dataset.inst_technology)
            .join_from(Organism, Taxa, Organism.inst_taxa)
            .where(Data.chrom == chrom, Data.start == start, Data.end == end)
        )
        query = self._add_modomics_ref_to_data_query(query)

        return {"records": [row._asdict() for row in self._session.execute(query)]}

    @staticmethod
    def _get_arg_sort(string: str, url_split: str = "%2B") -> str:
        col, order = string.split(url_split)
        return f"Data.{col}.{order}()"

    @staticmethod
    def _get_flt(string, url_split="%2B") -> tuple[str, list[str], str]:
        col, val, operator = string.split(url_split)
        return col, val.split(","), operator

    @staticmethod
    def _add_modomics_ref_to_data_query(query):
        return query.add_columns(Modomics.reference_id).join_from(
            Data, Modomics, Data.name == Modomics.short_name
        )

    def _get_length(self, query, model) -> int:
        return self._session.scalar(
            select(func.count()).select_from(query.with_only_columns(model.id))
        )

    @staticmethod
    def _get_base_search_query(isouter=False):
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
                func.group_concat(
                    GenomicAnnotation.id.distinct().op("ORDER BY")(GenomicAnnotation.id)
                ).label("gene_id"),
                func.group_concat(
                    GenomicAnnotation.name.distinct().op("ORDER BY")(
                        GenomicAnnotation.id
                    )
                ).label("gene_name"),
                func.group_concat(
                    GenomicAnnotation.biotype.distinct().op("ORDER BY")(
                        GenomicAnnotation.id
                    )
                ).label("gene_biotype"),
                DetectionTechnology.tech,
                Organism.taxa_id,
                Organism.cto,
            )
            .join_from(Data, DataAnnotation, Data.annotations, isouter=isouter)
            .join_from(
                DataAnnotation,
                GenomicAnnotation,
                DataAnnotation.inst_genomic,
                isouter=isouter,
            )
            .join_from(Data, Dataset, Data.inst_dataset)
            .join_from(Dataset, DetectionTechnology, Dataset.inst_technology)
            .join_from(Dataset, Organism, Dataset.inst_organism)
        )
        return query

    @staticmethod
    def _add_chrom_filters(query, chrom, start, end):
        query = query.where(Data.chrom == chrom)
        if start:
            query = query.where(Data.start >= start)
        if end:
            query = query.where(Data.end <= end)
        return query

    def _get_gene_filters(self, query, gene_filter, annotation):
        # gene filters: matchMode unused (cf. PrimeVue), but keep it this way
        # e.g. to extend options or add table filters
        # TODO annotation
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
        return query

    def _get_sort_filters(self, query, multi_sort):
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
        return query

    def _return_ensembl_query(
        self,
        annotation: Annotation,
        modification_id: int,
        organism_id: int,
        technology_ids: list[int],
        gene_filter: list[str],
        chrom: str | None,
        chrom_start: int | None,
        chrom_end: int | None,
        first_record: int | None,
        max_records: int | None,
        multi_sort: list[str],
    ):
        query = self._get_base_search_query(isouter=True)
        query = query.where(
            Data.modification_id == modification_id,
            Dataset.organism_id == organism_id,
            Dataset.technology_id.in_(technology_ids),
        )
        if chrom:
            query = self._add_chrom_filters(query, chrom, chrom_start, chrom_end)
        if gene_filter:
            query = self._get_gene_filters(query, gene_filter, annotation)
        query = query.group_by(Data.id)

        length = self._get_length(query, Data)

        query = self._get_sort_filters(query, multi_sort)

        if first_record is not None:
            query = query.offset(first_record)
        if max_records is not None:
            query = query.limit(max_records)

        query = self._add_modomics_ref_to_data_query(query)

        return query, length

    def _return_gene_query(
        self,
        annotation: Annotation,
        taxa_id: int,
        gene_filter: list[str],
        chrom: str | None,
        chrom_start: int | None,
        chrom_end: int | None,
        first_record: int | None,
        max_records: int | None,
        multi_sort: list[str],
    ):
        query = self._get_base_search_query()
        query = query.where(Organism.taxa_id == taxa_id)
        if chrom:
            query = self._add_chrom_filters(query, chrom, chrom_start, chrom_end)
        if gene_filter:
            query = self._get_gene_filters(query, gene_filter, annotation)
        query = query.group_by(Data.id)

        length = self._get_length(query, Data)

        query = self._get_sort_filters(query, multi_sort)

        if first_record is not None:
            query = query.offset(first_record)
        if max_records is not None:
            query = query.limit(max_records)

        query = self._add_modomics_ref_to_data_query(query)

        return query, length


@cache
def get_modification_service() -> ModificationService:
    """Instantiates a ModificationService object.

    :returns: ModificationService instance
    :rtype: ModificationService
    """
    return ModificationService(
        session=get_session(), annotation_service=get_annotation_service()
    )

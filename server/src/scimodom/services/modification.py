from functools import cache
from typing import Any, ClassVar

from sqlalchemy import select, func
from sqlalchemy.sql import Select
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
    BIOTYPES,
)
from scimodom.utils.specs.enums import AnnotationSource


class MultiSortError(Exception):
    """Exception handling for sort columns."""

    pass


class ModificationService:
    """Utility class to query modifications.

    :param session: SQLAlchemy ORM session
    :param annotation_service: Annotation service instance
    """

    SORT_COLUMNS: ClassVar[dict[str, Any]] = {
        "chrom": Data.chrom,
        "score": Data.score,
        "start": Data.start,
        "coverage": Data.coverage,
        "frequency": Data.frequency,
    }

    def __init__(self, session: Session, annotation_service: AnnotationService):
        self._session = session
        self._annotation_service = annotation_service

    # TODO MS14
    def get_modifications_by_source(
        self,
        annotation_source: AnnotationSource,
        modification_id: int,
        organism_id: int,
        technology_ids: list[int],
        taxa_id: int,
        gene_name: str | None,
        biotypes: list[str],
        features: list[str],
        chrom: str | None,
        chrom_start: int | None,
        chrom_end: int | None,
        first_record: int | None,
        max_records: int | None,
        multi_sort: list[str],
    ) -> dict[str, Any]:
        """Get Data records for Search query by modification.

        :param annotation_source: Source of annotation
        :param modification_id: Modification identifier
        :param organism_id: Organism identifier
        :param technology_ids: Technology identifier(s)
        :param taxa_id: Taxon identifier
        :param gene_name: Gene name filter (exact match)
        :param biotypes: Gene biotype filter (grouped/display categories)
        :param features: Annotation feature filter
        :param chrom: Chromosome filter
        :param chrom_start: Chromosome start filter
        :param chrom_end: Chromosome end filter
        :param first_record: first record
        :param max_records: number of records
        :param multi_sort: Table sort criteria
        :return: The records matching the given query parameters
        """
        annotation = self._annotation_service.get_annotation(annotation_source, taxa_id)
        if annotation_source == AnnotationSource.ENSEMBL:
            query, length = self._return_ensembl_query(
                annotation,
                modification_id,
                organism_id,
                technology_ids,
                gene_name,
                biotypes,
                features,
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

    # TODO MS14
    def get_modifications_by_gene(
        self,
        annotation_source: AnnotationSource,
        taxa_id: int,
        gene_name: str | None,
        biotypes: list[str],
        features: list[str],
        chrom: str | None,
        chrom_start: int | None,
        chrom_end: int | None,
        first_record: int | None,
        max_records: int | None,
        multi_sort: list[str],
    ) -> dict[str, Any]:
        """Get Data records for Search query by gene.

        :param annotation_source: Source of annotation
        :param taxa_id: Taxon identifier
        :param gene_name: Gene name filter (exact match)
        :param biotypes: Gene biotype filter (grouped/display categories)
        :param features: Annotation feature filter
        :param chrom: Chromosome filter
        :param chrom_start: Chromosome start filter
        :param chrom_end: Chromosome end filter
        :param first_record: first record
        :param max_records: number of records
        :param multi_sort: Table sort criteria
        :return: The records matching the given query parameters
        """
        annotation = self._annotation_service.get_annotation(annotation_source, taxa_id)
        if annotation_source == AnnotationSource.ENSEMBL:
            query, length = self._return_gene_query(
                annotation,
                taxa_id,
                gene_name,
                biotypes,
                features,
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
    def _get_flt(string, url_split="+") -> tuple[str, list[str], str]:
        col, val, operator = string.split(url_split)
        return col, val.split(","), operator

    @staticmethod
    def _add_modomics_ref_to_data_query(query):
        return query.add_columns(Modomics.reference_id).join_from(
            Data, Modomics, Data.name == Modomics.short_name
        )

    def _get_length(self, query, model) -> int:
        return self._session.execute(
            select(func.count()).select_from(
                query.with_only_columns(model.id).subquery()
            )
        ).scalar_one()

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
    def _add_chrom_filters(
        query: Select[Any],
        chrom: str,
        start: int,
        end: int,
    ) -> Select[Any]:
        query = query.where(Data.chrom == chrom)
        if start:
            query = query.where(Data.start >= start)
        if end:
            query = query.where(Data.end <= end)
        return query

    @staticmethod
    def _add_gene_filters(
        query: Select[Any],
        gene_name: str | None,
        biotypes: list[str],
        features: list[str],
        annotation: Annotation,
    ) -> Select[Any]:
        if gene_name:
            query = query.where(GenomicAnnotation.name == gene_name)
        if features:
            query = query.where(DataAnnotation.feature.in_(features))
        if biotypes:
            # 'biotypes' are the grouped/display categories; expand
            # to the raw values for the actual filter.
            # Index speedup on annotation.id, biotype, name.
            raw_biotypes = [key for key, value in BIOTYPES.items() if value in biotypes]
            query = query.where(GenomicAnnotation.annotation_id == annotation.id).where(
                GenomicAnnotation.biotype.in_(raw_biotypes)
            )
        return query

    @classmethod
    def _get_multi_sort(
        cls,
        query: Select[Any],
        multi_sort: list[str],
    ) -> Select[Any]:
        def _get_col_and_order(string: str, delim: str = "+"):
            col, order = string.split(delim)
            try:
                column = cls.SORT_COLUMNS[col]
            except KeyError:
                raise MultiSortError(f"Invalid sort column: '{col}'")
            if order == "asc":
                return column.asc()
            elif order == "desc":
                return column.desc()
            else:
                raise MultiSortError(f"Invalid sort direction: '{order}'")

        for sort in multi_sort:
            ordered_col = _get_col_and_order(sort)
            query = query.order_by(ordered_col)

        return query

    def _get_remaining_query(
        self,
        annotation: Annotation,
        gene_name: str | None,
        biotypes: list[str],
        features: list[str],
        chrom: str | None,
        chrom_start: int | None,
        chrom_end: int | None,
        first_record: int | None,
        max_records: int | None,
        multi_sort: list[str],
        query: Select[Any],
    ) -> tuple[Select[Any], int]:
        if chrom:
            query = self._add_chrom_filters(query, chrom, chrom_start, chrom_end)
        if gene_name or biotypes or features:
            query = self._add_gene_filters(
                query, gene_name, biotypes, features, annotation
            )
        query = query.group_by(Data.id)
        length = self._get_length(query, Data)
        query = self._get_multi_sort(query, multi_sort)
        if first_record is not None:
            query = query.offset(first_record)
        if max_records is not None:
            query = query.limit(max_records)
        query = self._add_modomics_ref_to_data_query(query)

        return query, length

    def _return_ensembl_query(
        self,
        annotation: Annotation,
        modification_id: int,
        organism_id: int,
        technology_ids: list[int],
        gene_name: str | None,
        biotypes: list[str],
        features: list[str],
        chrom: str | None,
        chrom_start: int | None,
        chrom_end: int | None,
        first_record: int | None,
        max_records: int | None,
        multi_sort: list[str],
    ) -> tuple[Select[Any], int]:
        query = self._get_base_search_query(isouter=True)
        query = query.where(
            Data.modification_id == modification_id,
            Dataset.organism_id == organism_id,
            Dataset.technology_id.in_(technology_ids),
        )
        return self._get_remaining_query(
            annotation,
            gene_name,
            biotypes,
            features,
            chrom,
            chrom_start,
            chrom_end,
            first_record,
            max_records,
            multi_sort,
            query,
        )

    def _return_gene_query(
        self,
        annotation: Annotation,
        taxa_id: int,
        gene_name: str | None,
        biotypes: list[str],
        features: list[str],
        chrom: str | None,
        chrom_start: int | None,
        chrom_end: int | None,
        first_record: int | None,
        max_records: int | None,
        multi_sort: list[str],
    ) -> tuple[Select[Any], int]:
        query = self._get_base_search_query()
        query = query.where(Organism.taxa_id == taxa_id)
        return self._get_remaining_query(
            annotation,
            gene_name,
            biotypes,
            features,
            chrom,
            chrom_start,
            chrom_end,
            first_record,
            max_records,
            multi_sort,
            query,
        )


@cache
def get_modification_service() -> ModificationService:
    """Instantiate a ModificationService object.

    :return: ModificationService instance
    """
    return ModificationService(
        session=get_session(), annotation_service=get_annotation_service()
    )

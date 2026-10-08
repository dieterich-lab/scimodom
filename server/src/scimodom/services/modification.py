from functools import cache
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar

from sqlalchemy import select, func, and_
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


@dataclass(kw_only=True)
class PageParams:
    """DTO for page, size, and sort parameters."""

    offset: int | None = None
    limit: int | None = None
    sort: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class SearchParams:
    """DTO for common search parameters."""

    gene_name: str | None = None
    biotypes: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    chrom: str | None = None
    chrom_start: int | None = None
    chrom_end: int | None = None


class MultiSortError(Exception):
    """Exception handling for sort columns."""

    pass


class ModificationService:
    """Utility class to query modifications.

    :param session: SQLAlchemy ORM session
    :param annotation_service: Annotation service instance
    """

    class SortOrder(Enum):
        """Provide table sort order."""

        ASC = "asc"
        DESC = "desc"

    SORT_COLUMNS: ClassVar[dict[str, Any]] = {
        "chrom": Data.chrom,
        "start": Data.start,
        "score": Data.score,
        "coverage": Data.coverage,
        "frequency": Data.frequency,
    }

    DEFAULT_SORT: ClassVar[tuple[str, ...]] = (
        "chrom+asc",
        "start+asc",
    )

    def __init__(self, session: Session, annotation_service: AnnotationService):
        self._session = session
        self._annotation_service = annotation_service

    # TODO MS14
    def get_modification_records_by_selection(
        self,
        annotation_source: AnnotationSource,
        taxa_id: int,
        modification_id: int,
        organism_id: int,
        technology_ids: list[int],
        search_params: SearchParams,
        page_params: PageParams,
    ) -> dict[str, Any]:
        """Get Data records for Search query (default).

        NOTE: The caller e.g. API is responsible for
        query semantics (gene_name XOR chrom, etc.).

        :param annotation_source: Source of annotation
        :param taxa_id: Taxon identifier
        :param modification_id: Modification identifier
        :param organism_id: Organism identifier
        :param technology_ids: Technology identifier(s)
        :param pagination_params: Pagination or sort parameters
        :param search_params: Secondary search parameters
        :return: The records matching the given query parameters
        """
        if annotation_source is not AnnotationSource.ENSEMBL:
            raise NotImplementedError(
                f"Annotation source '{annotation_source}' not implemented"
            )
        annotation = self._annotation_service.get_annotation(
            annotation_source,
            taxa_id,
        )
        query = self._build_query(annotation, search_params)
        query = query.where(
            Data.modification_id == modification_id,
            Dataset.organism_id == organism_id,
            Dataset.technology_id.in_(technology_ids),
        )
        query = self._prepare_query(
            query,
            annotation,
            search_params,
            page_params,
        )
        return self._execute_query(query, page_params.offset)

    # TODO MS14
    def get_modification_records_by_gene(
        self,
        annotation_source: AnnotationSource,
        taxa_id: int,
        search_params: SearchParams,
        page_params: PageParams,
    ) -> dict[str, Any]:
        """Get Data records for Search query "by gene".

        NOTE: The caller e.g. API is responsible for
        query semantics (gene_name XOR chrom, etc.).

        :param annotation_source: Source of annotation
        :param taxa_id: Taxon identifier
        :param gene_name: Gene name filter (exact match)
        :param pagination_params: Pagination or sort parameters
        :param search_params: Secondary search parameters
        :return: The records matching the given query parameters
        """
        if annotation_source is not AnnotationSource.ENSEMBL:
            raise NotImplementedError(
                f"Annotation source '{annotation_source}' not implemented"
            )
        annotation = self._annotation_service.get_annotation(
            annotation_source,
            taxa_id,
        )
        query = self._build_query(annotation, search_params)
        query = query.where(Organism.taxa_id == taxa_id)
        query = self._prepare_query(
            query,
            annotation,
            search_params,
            page_params,
        )
        return self._execute_query(query, page_params.offset)

    def get_modification_records_count(self) -> int:
        """Get total count of data records.

        Within a dataset, #records = #sites,
        but not across datasets.

        :return: The number of data records
        """
        return self._session.scalar(select(func.count()).select_from(Data))

    def get_modification_site(
        self,
        chrom: str,
        start: int,
        end: int,
    ) -> dict[str, list[dict[str, Any]]]:
        """Retrieve information related to a modification site.

        :param chrom: Chromosome
        :param chrom_start: Chromosome start
        :param chrom_end: Chromosome end
        :return: The query results
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
        query = self._add_modomics_ref(query)

        return {"records": [row._asdict() for row in self._session.execute(query)]}

    def get_modification_sites_count(self) -> int:
        """Get total count of modification sites.

        TODO: site table

        :return: The number of sites
        """
        site_query = select(
            Data.modification_id,
            Data.chrom,
            Data.start,
            Data.end,
            Data.strand,
        ).distinct()

        return self._session.scalar(
            select(func.count()).select_from(site_query.subquery())
        )

    @staticmethod
    def _get_raw_biotypes(biotypes: list[str]) -> list[str]:
        """Expand display-category biotypes to raw Ensembl biotypes."""
        return [key for key, value in BIOTYPES.items() if value in biotypes]

    @staticmethod
    def _add_modomics_ref(query: Select[Any]) -> Select[Any]:
        """Decorate query with Modomics reference.

        NOTE: The LEFT OUTER JOIN is only fail safe. It is
        equivalent to an INNER JOIN because every Data row
        has exactly one matching Modomics row (Data.name is
        a non-nullable FK to Modomics.short_name).
        """
        return query.add_columns(Modomics.reference_id).join_from(
            Data, Modomics, Data.name == Modomics.short_name, isouter=True
        )

    @staticmethod
    def _build_query(
        annotation: Annotation,
        search_params: SearchParams,
    ):
        """Construct the base data query.

        NOTE: This join only affects which of an already
        selected row's own annotations are displayed, never
        which rows are returned; that is done by the semi-join
        in `_apply_gene_filters`.

        - Data LEFT OUTER JOIN DataAnnotation: A Data row w/o
        annotation is always returned, but its ON clause restricts
        which DataAnnotation rows are displayed whenever "features"
        is active.

        - DataAnnotation LEFT OUTER JOIN GenomicAnnotation: Only
        when "gene_name" nor "biotypes" is active, else INNER JOIN.
        A DataAnnotation row whose GenomicAnnotation fails that
        filter must disappear from the display. This never wrongly
        drops a Data row that should still appear; the semi-join has
        already restricted the outer query, via WHERE, to Data.id values
        with at least one DataAnnotation row genuinely satisfying the
        same filter.
        """
        gene_name = search_params.gene_name
        biotypes = search_params.biotypes
        features = search_params.features

        data_annotation_on = Data.id == DataAnnotation.data_id
        if features:
            data_annotation_on = and_(
                data_annotation_on, DataAnnotation.feature.in_(features)
            )

        genomic_annotation_on = GenomicAnnotation.id == DataAnnotation.gene_id
        genomic_annotation_isouter = True
        if gene_name or biotypes or features:
            # match semi-join in `_apply_gene_filters`
            genomic_annotation_on = and_(
                genomic_annotation_on,
                GenomicAnnotation.annotation_id == annotation.id,
            )
        if gene_name or biotypes:
            # gene-level filter requires a matching genomic_annotation
            genomic_annotation_isouter = False
        if gene_name:
            genomic_annotation_on = and_(
                genomic_annotation_on, GenomicAnnotation.name == gene_name
            )
        if biotypes:
            genomic_annotation_on = and_(
                genomic_annotation_on,
                GenomicAnnotation.biotype.in_(
                    ModificationService._get_raw_biotypes(biotypes)
                ),
            )

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
            .join_from(Data, DataAnnotation, data_annotation_on, isouter=True)
            .join_from(
                DataAnnotation,
                GenomicAnnotation,
                genomic_annotation_on,
                isouter=genomic_annotation_isouter,
            )
            .join_from(Data, Dataset, Data.inst_dataset)
            .join_from(Dataset, DetectionTechnology, Dataset.inst_technology)
            .join_from(Dataset, Organism, Dataset.inst_organism)
        )
        return query

    @staticmethod
    def _apply_chrom_filters(
        query: Select[Any],
        search_params: SearchParams,
    ) -> Select[Any]:
        if search_params.chrom is None:
            return query
        query = query.where(Data.chrom == search_params.chrom)
        if search_params.chrom_start is not None:
            query = query.where(Data.start >= search_params.chrom_start)
            if search_params.chrom_end is not None:
                query = query.where(Data.end <= search_params.chrom_end)
        return query

    @staticmethod
    def _apply_gene_filters(
        query: Select[Any],
        annotation: Annotation,
        search_params: SearchParams,
    ) -> Select[Any]:
        """Restrict query to Data rows with matching annotation.

        NOTE: Perform a semi-join against a separate
        DataAnnotation/GenomicAnnotation subquery, not a WHERE
        clause against the LEFT JOIN already present (keeps row
        selection and row display independent). A WHERE
        would narrow the joined rows, not the Data rows, forcing
        the full display join to run before any filtering can
        happen (implicitly turning it into an INNER JOIN),
        rather than letting the filter narrow Data.id first.
        """
        gene_name = search_params.gene_name
        biotypes = search_params.biotypes
        features = search_params.features

        if not (gene_name or features or biotypes):
            return query

        # avoid gene_name/feature/biotype to match a stale release
        subquery = (
            select(DataAnnotation.data_id)
            .join_from(
                DataAnnotation,
                GenomicAnnotation,
                DataAnnotation.inst_genomic,
            )
            .where(GenomicAnnotation.annotation_id == annotation.id)
        )
        if gene_name:
            subquery = subquery.where(GenomicAnnotation.name == gene_name)
        if features:
            subquery = subquery.where(DataAnnotation.feature.in_(features))
        if biotypes:
            subquery = subquery.where(
                GenomicAnnotation.biotype.in_(
                    ModificationService._get_raw_biotypes(biotypes)
                )
            )
        return query.where(Data.id.in_(subquery))

    @staticmethod
    def _apply_paginate(
        query: Select[Any],
        page_params: PageParams,
    ) -> Select[Any]:
        if page_params.offset is not None:
            query = query.offset(page_params.offset)
        if page_params.limit is not None:
            query = query.limit(page_params.limit)
        return query

    @classmethod
    def _apply_sort(
        cls,
        query: Select[Any],
        page_params: PageParams,
    ) -> Select[Any]:
        def _get_col_and_order(string: str, delim: str = "+"):
            try:
                col, order = string.split(delim)
                column = cls.SORT_COLUMNS[col]
            except ValueError as exc:
                raise MultiSortError(f"Invalid sort: '{string}'") from exc
            except KeyError as exc:
                raise MultiSortError(f"Invalid sort column: '{col}'") from exc
            if order == cls.SortOrder.ASC.value:
                return column.asc()
            if order == cls.SortOrder.DESC.value:
                return column.desc()
            raise MultiSortError(f"Invalid sort direction: '{order}'")

        sort = page_params.sort or list(cls.DEFAULT_SORT)
        for this_sort in sort:
            ordered_col = _get_col_and_order(this_sort)
            query = query.order_by(ordered_col)

        return query

    def _prepare_query(
        self,
        query: Select[Any],
        annotation: Annotation,
        search_params: SearchParams,
        page_params: PageParams,
    ) -> Select[Any]:
        query = self._add_modomics_ref(query)
        query = self._apply_chrom_filters(query, search_params)
        query = self._apply_gene_filters(query, annotation, search_params)
        query = query.group_by(Data.id)
        query = query.add_columns(func.count().over().label("total_count"))
        query = self._apply_sort(query, page_params)
        query = self._apply_paginate(query, page_params)

        return query

    def _get_fallback_count(self, query: Select[Any]) -> int:
        count_query = (
            query.with_only_columns(Data.id)
            .order_by(None)
            .group_by(None)
            .distinct()
            .offset(None)
            .limit(None)
        )
        return self._session.scalar(
            select(func.count()).select_from(count_query.subquery())
        )

    def _execute_query(self, query: Select[Any], offset: int | None) -> dict[str, Any]:
        rows = self._session.execute(query).all()
        if rows:
            total = rows[0].total_count
            records = [
                {k: v for k, v in row._asdict().items() if k != "total_count"}
                for row in rows
            ]
            return {"totalRecords": total, "records": records}
        # 0 matches - implicitly assumes that LIMIT can't be 0
        if offset is None or offset == 0:
            return {"totalRecords": 0, "records": []}
        # offset > 0: truly 0 matches, or OFFSET
        # is past last page - fall back to real COUNT
        total = self._get_fallback_count(query)
        return {"totalRecords": total, "records": []}


@cache
def get_modification_service() -> ModificationService:
    """Instantiate a ModificationService object.

    :return: ModificationService instance
    """
    return ModificationService(
        session=get_session(), annotation_service=get_annotation_service()
    )

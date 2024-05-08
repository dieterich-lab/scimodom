from collections.abc import Sequence
from logging import getLogger
from pathlib import Path
from typing import Any, Optional, Literal, get_args

from sqlalchemy import select
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import Data, Association
from scimodom.utils.operations import to_bedtool, _remove_extra_feature
from scimodom.services.importer import get_bed_importer
import scimodom.utils.utils as utils

logger = getLogger(__name__)


class FailedUploadError(Exception):
    pass


class NoRecordsFoundError(Exception):
    pass


class ComparisonService:
    """Utility class to handle dataset comparison.
    The EUFID(s) are assumed to be well-defined,
    avoiding repeated validation queries to the
    database.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param reference_ids: Reference EUFID(s)
    :type reference_ids: list of str
    :param comparison_ids: EUFID(s) to compare
    :type comparison_ids: list of str
    :param query_operation: Comparison to perform:
    intersect, closest, or subtract (difference)
    :type query_operation: str
    :param is_strand: Perform strand-aware query
    :type is_strand: bool
    """

    OPERATIONS = Literal["intersect", "closest", "subtract"]

    def __init__(
        self,
        session: Session,
        reference_ids: list[str],
        comparison_ids: list[str],
        query_operation: OPERATIONS,
        is_strand: bool,
    ) -> None:
        """Initializer method."""
        self._session = session
        self._reference_ids = reference_ids
        self._comparison_ids = comparison_ids
        self._query_operation = query_operation
        self._is_strand = is_strand

        self._reference_records: Sequence[Any]
        self._comparison_records: Sequence[Any]

        operations = get_args(self.OPERATIONS)
        assert (
            query_operation in operations
        ), f"Undefined '{query_operation}'. Allowed values are {operations}."

    @classmethod
    def from_upload(
        cls,
        session: Session,
        reference_ids: list[str],
        query_operation: str,
        is_strand: bool,
        upload: str | Path,
    ):
        """Provides ComparisonService factory to
        instantiate class upload instead of EUFID(s).

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param reference_ids: Reference EUFID(s)
        :type reference_ids: list of str
        :param upload: Uploaded dataset to compare
        :type upload: str | Path
        :param query_operation: Comparison to perform:
        intersect, closest, or subtract (difference)
        :type query_operation: str
        :param is_strand: Perform strand-aware query
        :type is_strand: bool
        """
        upload_path = Path(upload)
        if not upload_path.is_file():
            msg = f"No such file or directory: {upload_path.as_posix()}"
            raise FileNotFoundError(msg)
        try:
            db_records = ComparisonService.upload_file()
        except Exception as exc:
            # upload itself is "fail-safe", catch eveything else...
            msg = f"Failed to upload {upload_path.as_posix()}. "
            raise FailedUploadError(msg)
        records = [tuple([val for key, val in record.items()]) for record in db_records]
        # ... but records might be "skipped" for various reasons
        if not records:
            raise NoRecordsFoundError
        service = cls(session, reference_ids, [], query_operation, is_strand)
        service._comparison_records = records
        return service

    @staticmethod
    def upload_file(file_path: Path) -> list[dict[str, Any]]:
        """Upload bed-like file.

        :param file_path: Path to file
        :type file_path: Path
        :return: Uploaded records
        :rtype: list of dict of {str: Any}
        """
        importer = get_bed_importer(file_path)
        importer.parse_records()
        importer.close()
        return importer.get_buffer()

    def get_records(self) -> None:
        """Query the database for selected records."""

        def _construct_query(idx):
            query = (
                select(
                    Data.chrom,
                    Data.start,
                    Data.end,
                    Data.name,
                    Data.score,
                    Data.strand,
                    Association.dataset_id,
                    Data.coverage,
                    Data.frequency,
                )
                .join_from(Data, Association, Data.inst_association)
                .where(Association.dataset_id.in_(idx))
            )
            return query

        query = _construct_query(self._reference_ids)
        self._reference_records = self._session.execute(query).all()

        if self._comparison_ids:
            self._comparison_records = []
            for idx in self._comparison_ids:
                query = _construct_query([idx])
                self._comparison_records.append(self._session.execute(query).all())

        # check for empty records?

    def compare_dataset(self):  # ->
        """Execute comparison.

        :return: Result form comparison
        :rtype:
        """
        func = eval(f"_get_{self._query_operation}")
        records = func(self._reference_records, self._comparison_records)

        # TODO
        # from scimodom.utils.models import records_factory
        # op, strand = query_operation.split("S")
        # c_records = get_op(op)(a_records, b_records, s=eval(strand))
        # records = [records_factory(op.capitalize(), r)._asdict() for r in c_records]

        return records

    def _get_intersect(
        a_records: Sequence[Any],
        b_records: Sequence[Any],
        s: bool = True,
        sorted: bool = True,
    ) -> list[Any]:
        """Wrapper for pybedtools.bedtool.BedTool.intersect

        Relies on the behaviour of bedtools -wa -wb option: the first
        column after the complete -a record lists the file number
        from which the overlap came.

        :param a_records: DB records (A features)
        :type a_records: Sequence (list of tuples)
        :param b_records: DB records (B features)
        :type b_records: Sequence (list of tuples)
        :param s: Force strandedness
        :type s: bool
        :param sorted: Invoked sweeping algorithm
        :type sorted: bool
        :returns: records
        :rtype: list of tuples
        """

        # required options
        # write the original entry in A for each overlap
        wa: bool = True
        # write the original entry in B for each overlap
        wb: bool = True

        a_bedtool, b_bedtool = to_bedtool(a_records), to_bedtool(
            b_records, as_list=True
        )
        bedtool = a_bedtool.intersect(
            b=[b.fn for b in b_bedtool], wa=wa, wb=wb, s=s, sorted=sorted
        )
        stream = bedtool.each(_remove_extra_feature)
        records = [tuple(s.fields) for s in stream]
        return records

    def _get_closest(
        a_records: Sequence[Any],
        b_records: Sequence[Any],
        s: bool = True,
        sorted: bool = True,
    ) -> list[Any]:
        """Wrapper for pybedtools.bedtool.BedTool.closest

        Relies on the behaviour of bedtools -io -t -mdb -D options: the first
        column after the complete -a record lists the file number
        from which the closest interval came.

        :param a_records: DB records (A features)
        :type a_records: Sequence (list of tuples)
        :param b_records: DB records (B features)
        :type b_records: Sequence (list of tuples)
        :param s: Force strandedness
        :type s: bool
        :param sorted: Invoked sweeping algorithm
        :type sorted: bool
        :returns: records
        :rtype: list of tuples
        """

        # required options
        # Ignore features in B that overlap A
        io: bool = True
        # Report all ties
        t: str = "all"
        # Report closest records among all databases
        mdb: str = "all"
        # Report distance with respect to A
        D: str = "a"

        a_bedtool, b_bedtool = to_bedtool(a_records), to_bedtool(
            b_records, as_list=True
        )
        bedtool = a_bedtool.closest(
            b=[b.fn for b in b_bedtool], io=io, t=t, mdb=mdb, D=D, s=s, sorted=sorted
        )
        stream = bedtool.each(_remove_extra_feature)
        records = [tuple(s.fields) for s in stream]

        # TODO
        # Reports “none” for chrom (?) and “-1” for all other fields (?) when a feature
        # is not found in B on the same chromosome as the feature in A.
        # Note that "start" (fields) is a string!
        # 9 + 0/1 + 1
        # c_bedtool = c_bedtool.filter(lambda c: c.fields[(offset + filnum_idx + 1)] != "-1")

        return records

    def _get_subtract(
        a_records: Sequence[Any],
        b_records: Sequence[Any],
        s: bool = True,
        sorted: bool = True,
    ) -> list[Any]:
        """Wrapper for pybedtools.bedtool.BedTool.subtract

        :param a_records: DB records (A features)
        :type a_records: Sequence (list of tuples)
        :param b_records: DB records (B features)
        :type b_records: Sequence (list of tuples)
        :param s: Force strandedness
        :type s: bool
        :param sorted: Invoked sweeping algorithm
        :type sorted: bool
        :param n_fields: Number of other fields attribute in addition to BED6
        :type n_fields: int
        :returns: records
        :rtype: list of tuples
        """

        a_bedtool, b_bedtool = to_bedtool(a_records), to_bedtool(
            utils.flatten_list(b_records)
        )
        c_bedtool = a_bedtool.subtract(b_bedtool, s=s, sorted=sorted)
        # records = [(i.fields[:offset]) for i in c_bedtool]
        # TODO ??? offset = 6 + 3
        # records = [tuple(i.fields[:offset]) for i in c_bedtool]
        # return records


_cached_service: Optional[ComparisonService] = None


def get_comparison_service() -> ComparisonService:
    global _cached_service
    if _cached_service is None:
        # TODO
        # _cached_service = ComparisonService(session=get_session())
        pass
    return _cached_service

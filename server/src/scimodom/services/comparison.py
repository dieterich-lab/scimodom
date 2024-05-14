from collections.abc import Sequence
from logging import getLogger
from pathlib import Path
from typing import Any, Optional, Literal, ClassVar, get_args

from sqlalchemy import select
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import Data, Association
from scimodom.utils.operations import to_bedtool, _remove_filno
from scimodom.utils.models import records_factory
from scimodom.services.importer import get_bed_importer
from scimodom.utils.specifications import SPECS_EUF
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
    """

    OPERATIONS = Literal["intersect", "closest", "subtract"]
    # must match exactly incl. order of utils.models
    COLUMNS: ClassVar[list[str]] = [
        v
        for k, v in SPECS_EUF[SPECS_EUF["versions"][-1]]["columns"].items()
        if k not in ["thickStart", "thickEnd", "itemRgb"]
    ]
    COLUMNS.insert(6, "dataset_id")

    def __init__(self, session: Session) -> None:
        """Initializer method."""
        self._session = session

        self._query_operation: str
        self._is_strand: bool
        self._reference_records: Sequence[Any]
        self._comparison_records: Sequence[Any]

    @staticmethod
    def upload_file(file_path: Path, is_euf: bool) -> list[dict[str, Any]]:
        """Upload bed-like file.

        :param file_path: Path to file
        :type file_path: Path
        :param is_euf: BED6 or bedRMod (EUF)
        :type is_euf: bool
        :return: Uploaded records
        :rtype: list of dict of {str: Any}
        """

        def _patch_upload(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
            """Patch BED6 or bedRMod for comparison."""
            fields = {"dataset_id": "Upload"}
            if not is_euf:
                fields = fields | {"coverage": 0, "frequency": 0}
            return [r | fields for r in records]

        importer = get_bed_importer(file_path, is_euf=is_euf)
        importer.parse_records()
        importer.close()
        return _patch_upload(importer.get_buffer())

    def query_reference_records(self, ids: list[str]) -> None:
        """Query the database for reference records.

        :param ids: EUFID(s)
        :type ids: list of str
        """

        def _construct_query(ids: list[str]):
            """Query constructor.

            :param ids: EUFID(s)
            :type ids: list of str
            :return: Query
            :rtype: SQLAlchemy query
            """
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
                .where(Association.dataset_id.in_(ids))
            )
            return query

        query = _construct_query(ids)
        records = self._session.execute(query).all()
        if not records:
            raise NoRecordsFoundError
        self._reference_records = records

    def query_comparison_records(self, ids: list[str]) -> None:
        """Query the database for comparison records.

        :param ids: EUFID(s)
        :type ids: list of str
        """

        def _construct_query(idx: str):
            """Query constructor.

            :param idx: EUFID
            :type idx: str
            :return: Query
            :rtype: SQLAlchemy query
            """
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
                .where(Association.dataset_id == idx)
            )
            return query

        self._comparison_records = []
        for idx in ids:
            query = _construct_query(idx)
            records = self._session.execute(query).all()
            if not records:
                raise NoRecordsFoundError
            self._comparison_records.append(records)

    def upload_records(self, upload: str, is_euf: bool):
        """Upload records.

        :param upload: Uploaded dataset to compare
        :type upload: str | Path
        :param is_euf: BED6 or bedRMod (EUF)
        :type is_euf: bool
        """
        upload_path = Path(upload)
        if not upload_path.is_file():
            msg = f"No such file or directory: {upload_path.as_posix()}"
            raise FileNotFoundError(msg)
        try:
            db_records = ComparisonService.upload_file(upload_path, is_euf)
        except Exception as exc:
            # upload itself is "fail-safe", catch eveything else...
            msg = f"Failed to upload {upload_path.as_posix()}. "
            raise FailedUploadError(msg)
        records = [
            tuple([record[key] for key in self.COLUMNS]) for record in db_records
        ]
        # ... but records might be "skipped" for various reasons
        if not records:
            raise NoRecordsFoundError
        # comparison records is a list of list (records) - for a rationale
        # cf. how pybedtools deals with multiple "files" for intersect and subtract
        self._comparison_records = [records]

    def compare_dataset(self):  # ->
        """Execute comparison.

        :return: Records
        :rtype: List of dict
        """
        func = eval(f"self._{self._query_operation}")
        records = [
            records_factory(self._query_operation.capitalize(), r)._asdict()
            for r in func()
        ]
        return records

    def _intersect(self, is_sorted: bool = True) -> list[Any]:
        """Wrapper for pybedtools.bedtool.BedTool.intersect

        Relies on the behaviour of bedtools -wa -wb option: the first
        column after the complete -a record lists the file number
        from which the overlap came.

        :param is_sorted: Invoked sweeping algorithm
        :type is_sorted: bool
        :returns: records
        :rtype: list of tuples
        """

        # required options
        # write the original entry in A for each overlap
        wa: bool = True
        # write the original entry in B for each overlap
        wb: bool = True

        a_bedtool = to_bedtool(self._reference_records)
        b_bedtool = to_bedtool(self._comparison_records, as_list=True)
        bedtool = a_bedtool.intersect(
            b=[b.fn for b in b_bedtool],
            wa=wa,
            wb=wb,
            s=self._is_strand,
            sorted=is_sorted,
        )
        stream = bedtool.each(_remove_filno)
        return [tuple(s.fields) for s in stream]

    def _closest(self, is_sorted: bool = True) -> list[Any]:
        """Wrapper for pybedtools.bedtool.BedTool.closest

        Relies on the behaviour of bedtools -io -t -mdb -D options: the first
        column after the complete -a record lists the file number
        from which the closest interval came.

        :param is_sorted: Invoked sweeping algorithm
        :type is_sorted: bool
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

        # BED6+3
        n_fields = 9

        a_bedtool = to_bedtool(self._reference_records)
        b_bedtool = to_bedtool(self._comparison_records, as_list=True)
        bedtool = a_bedtool.closest(
            b=[b.fn for b in b_bedtool],
            io=io,
            t=t,
            mdb=mdb,
            D=D,
            s=self._is_strand,
            sorted=is_sorted,
        )
        # Reports “none” for chrom (.) and “-1” for all other fields (start/end) when a feature
        # is not found in B on the same chromosome as the feature in A.
        stream = bedtool.each(_remove_filno, is_closest=True).filter(
            lambda c: c.fields[n_fields + 1] != "-1"
        )
        return [tuple(s.fields) for s in stream]

    def _subtract(self, is_sorted: bool = True) -> list[Any]:
        """Wrapper for pybedtools.bedtool.BedTool.subtract

        :param is_sorted: Invoked sweeping algorithm
        :type is_sorted: bool
        :returns: records
        :rtype: list of tuples
        """

        a_bedtool = to_bedtool(self._reference_records)
        b_bedtool = to_bedtool(utils.flatten_list(self._comparison_records))
        bedtool = a_bedtool.subtract(b_bedtool, s=self._is_strand, sorted=is_sorted)
        return [tuple(s.fields) for s in bedtool]

    def _init(
        self,
        query_operation: OPERATIONS,
        is_strand: bool,
    ) -> None:
        """Force initialize when a cached service
        exists but there is a change in parameters.

        :param query_operation: Comparison to perform:
        intersect, closest, or subtract (difference)
        :type query_operation: str
        :param is_strand: Perform strand-aware query
        :type is_strand: bool
        """
        self._query_operation = query_operation
        self._is_strand = is_strand

        operations = get_args(self.OPERATIONS)
        assert (
            query_operation in operations
        ), f"Undefined '{query_operation}'. Allowed values are {operations}."


_cached_comparison_service: Optional[ComparisonService] = None


def get_comparison_service(query_operation: str, is_strand: bool) -> ComparisonService:
    """Instantiate a ComparisonService.

    :param query_operation: Comparison to perform:
    intersect, closest, or subtract (difference)
    :type query_operation: str
    :param is_strand: Perform strand-aware query
    :type is_strand: bool
    :return: ComparisonService instance
    :rtype: ComparisonService
    """
    global _cached_comparison_service
    if _cached_comparison_service is None:
        _cached_comparison_service = ComparisonService(session=get_session())
    _cached_comparison_service._init(query_operation, is_strand)
    return _cached_comparison_service

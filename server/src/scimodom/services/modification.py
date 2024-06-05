from functools import cache
from typing import Union, List, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import Data, Association, Dataset
from scimodom.utils.bedtools_dto import ModificationRecord


class ModificationService:
    def __init__(self, session: Session):
        self._db_session = session

    def get_modifications_by_dataset(
        self, datasets: Union[str, Dataset, List[Union[str, Dataset]]]
    ) -> Iterable[ModificationRecord]:
        dataset_ids = self._get_datasets_as_id_list(datasets)

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
            .execution_options(yield_per=1000)
            .join_from(Data, Association, Data.inst_association)
            .where(Association.dataset_id.in_(dataset_ids))
        )
        stmt = self._db_session.execute(query)
        while True:
            row = stmt.fetchone()
            if row is None:
                return
            yield ModificationRecord(
                chrom=row.chrom,
                start=row.start,
                end=row.end,
                name=row.name,
                score=row.score,
                strand=row.strand,
                dataset_id=row.dataset_id,
                coverage=row.coverage,
                frequency=row.frequency,
            )

    @staticmethod
    def _get_datasets_as_id_list(datasets):
        if type(datasets) is str or isinstance(datasets, Dataset):
            datasets = [datasets]
        return [x.id if isinstance(x, Dataset) else x for x in datasets]


@cache
def get_modification_service():
    return ModificationService(session=get_session())

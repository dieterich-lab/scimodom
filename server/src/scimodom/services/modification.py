from functools import cache
from typing import Union, List, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import Data, Dataset
from scimodom.utils.bedtools_dto import ModificationRecord


class DataService:
    def __init__(self, session: Session):
        self._db_session = session

    def get_modifications_by_dataset(
        self, datasets: Union[str, Dataset, List[Union[str, Dataset]]]
    ) -> Iterable[ModificationRecord]:
        dataset_ids = self._get_datasets_as_id_list(datasets)

        query = (
            select(
                Data.id,
                Data.chrom,
                Data.start,
                Data.end,
                Data.name,
                Data.score,
                Data.strand,
                Data.dataset_id,
                Data.coverage,
                Data.frequency,
            )
            .execution_options(yield_per=1000)
            .where(Data.dataset_id.in_(dataset_ids))
        )
        stmt = self._db_session.execute(query)
        while True:
            row = stmt.fetchone()
            if row is None:
                return
            yield ModificationRecord(
                id=row.id,
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
    return DataService(session=get_session())

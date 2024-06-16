import logging
from functools import cache
from typing import Union, List, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import Data, Dataset

logger = logging.getLogger(__name__)


class NoDataRecords(Exception):
    pass


class DataService:
    def __init__(self, session: Session):
        self._db_session = session

    def get_by_dataset(
        self, datasets: Union[str, Dataset, List[Union[str, Dataset]]]
    ) -> Iterable[Data]:
        dataset_ids = self._get_datasets_as_id_list(datasets)

        query = (
            select(Data)
            .execution_options(yield_per=1000)
            .where(Data.dataset_id.in_(dataset_ids))
        )
        stmt = self._db_session.execute(query)
        count = 0
        while True:
            row = stmt.fetchone()
            if row is None:
                if count == 0:
                    raise NoDataRecords(
                        f"No records found for dataset id(s) {', '.join(dataset_ids)}!"
                    )
                return
            count += 1
            yield row

    @staticmethod
    def _get_datasets_as_id_list(datasets):
        if type(datasets) is str or isinstance(datasets, Dataset):
            datasets = [datasets]
        return [x.id if isinstance(x, Dataset) else x for x in datasets]


@cache
def get_data_service():
    return DataService(session=get_session())

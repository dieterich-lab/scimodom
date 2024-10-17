import pytest

from scimodom.services.data import DataService, NoDataRecords
from scimodom.utils.specs.enums import Strand


def test_get_by_dataset(dataset, Session):  # noqa
    service = DataService(session=Session())
    records = list(service.get_by_dataset("d1"))
    assert len(records) == 2
    assert records[0].chrom == "17"
    assert records[0].strand == Strand.FORWARD
    assert records[1].score == 900
    assert records[1].strand == Strand.REVERSE


def test_get_by_dataset_no_records(Session):
    service = DataService(session=Session())
    with pytest.raises(NoDataRecords) as exc:
        # get values from generator, otherwise this raises no error!
        list(service.get_by_dataset(["XXXXXXXXXXXX"]))
    assert str(exc.value) == "No records found for dataset id(s) XXXXXXXXXXXX!"

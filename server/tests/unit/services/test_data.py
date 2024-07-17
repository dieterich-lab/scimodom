from scimodom.services.data import DataService
from scimodom.utils.common_dto import Strand


def test_data_service_simple(dataset, Session):  # noqa
    service = DataService(session=Session())
    records = list(service.get_by_dataset(["d1"]))
    assert len(records) == 2
    assert records[0].chrom == "17"
    assert records[0].strand == Strand.FORWARD
    assert records[1].score == 900
    assert records[1].strand == Strand.REVERSE

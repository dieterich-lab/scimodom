from fixtures.dataset import dataset  # noqa
from scimodom.services.modification import DataService
from scimodom.utils.bedtools_dto import ModificationRecord, Strand


def test_modification_service_simple(dataset, Session):  # noqa
    service = DataService(session=Session())
    records = list(service.get_modifications_by_dataset(["d1"]))
    assert records == [
        ModificationRecord(
            id=1,
            chrom="17",
            start=100001,
            end=120000,
            name="Y",
            score=1000,
            strand=Strand.FORWARD,
            coverage=43,
            frequency=100,
            dataset_id="d1",
        ),
        ModificationRecord(
            id=2,
            chrom="Y",
            start=200001,
            end=220000,
            name="X",
            score=900,
            strand=Strand.REVERSE,
            coverage=44,
            frequency=99,
            dataset_id="d1",
        ),
    ]

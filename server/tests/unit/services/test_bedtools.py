from scimodom.services.bedtools import BedToolsService
from scimodom.utils.bedtools_dto import ModificationRecord, Strand


def test_get_modification_from_bedtools_data():
    record = BedToolsService._get_modification_from_bedtools_data(
        ["1", "1043431", "1043432", "Y", "190", "+", "iMuwPsi24Yka", "576", "19"]
    )
    assert isinstance(record, ModificationRecord)
    assert record.chrom == "1"
    assert record.start == 1043431
    assert record.end == 1043432
    assert record.name == "Y"
    assert record.score == 190
    assert record.strand == Strand.FORWARD
    assert record.dataset_id == "iMuwPsi24Yka"
    assert record.coverage == 576
    assert record.frequency == 19

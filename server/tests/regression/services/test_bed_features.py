import pytest

from scimodom.services.bedtools import BedToolsService

# from scimodom.utils.bedtools_dto import (
#     IntersectRecord,
#     ClosestRecord,
#     SubtractRecord,
#     ComparisonRecord,
#     Bed6Record,
# )
# from scimodom.utils.common_dto import Strand


def _add_tmp_data(tmp_path):
    # NOTE: subject to change cf. #119
    with open(tmp_path / "chrom.sizes", "w") as fh:
        fh.write("1\t248956422\n")


@pytest.fixture
def _get_bedtools_service(tmp_path):
    return BedToolsService(tmp_path=tmp_path)


def test_ensembl_to_bed_features(Session):
    pass

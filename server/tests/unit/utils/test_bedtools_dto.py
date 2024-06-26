from scimodom.utils.bedtools_dto import IntersectRecord, ComparisonRecord
from scimodom.utils.common_dto import Strand


def test_intersect_record():
    a = ComparisonRecord(
        chrom="a1",
        start=10,
        end=20,
        name="A1 the Great",
        score=105,
        strand=Strand.FORWARD,
        eufid="afsdfasd1234",
        coverage=17,
        frequency=17,
    )
    b = ComparisonRecord(
        chrom="b1",
        start=100,
        end=120,
        name="B1 the Tiny",
        score=500,
        strand=Strand.REVERSE,
        eufid="afsdfasd1234",
        coverage=100,
        frequency=27,
    )
    i = IntersectRecord(a=a, b=b)
    assert i.a.end == 20
    assert i.b.strand == Strand.REVERSE

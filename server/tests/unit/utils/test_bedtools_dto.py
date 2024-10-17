from collections import namedtuple

import pytest
from pydantic import ValidationError

from scimodom.utils.dtos.bedtools import (
    Bed6Record,
    EufRecord,
    ComparisonRecord,
    IntersectRecord,
    GenomicAnnotationRecord,
    DataAnnotationRecord,
)
from scimodom.utils.specs.enums import Strand

Bed6Fields = namedtuple("Bed6Fields", "chrom start end name score strand")
EufFields = namedtuple("EufFields", "start end coverage frequency")


@pytest.mark.parametrize(
    "fields",
    [
        Bed6Fields(1, 1, 2, "m6A", 0, Strand.FORWARD),
        Bed6Fields("1", 2, 1, "m6A", 0, Strand.FORWARD),
        Bed6Fields("1", -1, 2, "m6A", 0, Strand.FORWARD),
        Bed6Fields("1", 1, 2, "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", 0, Strand.FORWARD),
        Bed6Fields("1", 1, 2, "m6A", 1001, Strand.FORWARD),
        Bed6Fields("1", 1, 2, "m6A", 1000, "s"),
    ],
)
def test_bed6_record(fields):
    with pytest.raises(ValidationError):
        Bed6Record(
            chrom=fields.chrom,
            start=fields.start,
            end=fields.end,
            name=fields.name,
            score=fields.score,
            strand=fields.strand,
        )


@pytest.mark.parametrize(
    "fields",
    [
        EufFields(-1, 2, 0, 100),
        EufFields(2, 1, 0, 100),
        EufFields(1, 2, 0.5, 100),
        EufFields(1, 2, 0, 0.5),
        EufFields(1, 2, 0, 500),
    ],
)
def test_euf_record(fields):
    with pytest.raises(ValidationError):
        EufRecord(
            chrom="1",
            start=1,
            end=100,
            name="m6A",
            score=0,
            strand="+",
            thick_start=fields.start,
            thick_end=fields.end,
            item_rgb="0,0,0",
            coverage=fields.coverage,
            frequency=fields.frequency,
        )


def test_comparison_record():
    with pytest.raises(ValidationError):
        ComparisonRecord(
            chrom="1",
            start=10,
            end=20,
            name="m6A",
            score=0,
            strand=Strand.FORWARD,
            eufid="X",
            coverage=0,
            frequency=100,
        )


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


@pytest.mark.parametrize(
    "string,idx",
    [
        (
            "FGIBGV2VB927FN9ST2G1VV7GNLZD6P54NNJVOKU7TC5W8LDY94G5GXLTDAVRJLBBHRXY4H8E5WHAPD1A5NJZGL68O6ZOCFAXWOQ4SBODC9KECUTHOOZV1MUDWYMHZTEFCBGXC01QZXTQG4K0TK9DF0WQFP6PRHLHJO3GA3V30A15OOSISW545T9AY83Q4LNWSYZTKEV9Y0PA1ALWU1YYC30DUWJHTTE8U9A2SRC4FWCBLYJK62WV6",
            1,
        ),
        ("GENE_ID_OR_NAME", -1),
    ],
)
def test_genomic_annotation_record(string, idx):
    with pytest.raises(ValidationError):
        GenomicAnnotationRecord(id=string, annotation_id=idx, name=string, biotype=None)


@pytest.mark.parametrize(
    "idx, feature",
    [
        ("", "feature"),
        ("GENE_ID", "763HFOFU22YHESFX588LB3RE6C0WANJKFSWMBUXQSZ6DCBB26YWR"),
    ],
)
def test_data_annotation_record(idx, feature):
    with pytest.raises(ValidationError):
        DataAnnotationRecord(
            gene_id=idx,
            data_id=1,
            feature=feature,
        )

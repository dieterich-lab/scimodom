from pathlib import Path
import tempfile

import pytest

from scimodom.utils.operations import get_genomic_annotation
from scimodom.utils.operations import get_op


def _get_records(operation):
    a = [
        ("1", 101, 102, "m6A", 1, "+", "KEyK5s3pcKjE", 0, 0),
        ("1", 199, 200, "m6A", 2, "+", "KEyK5s3pcKjE", 0, 0),
        ("1", 200, 201, "m6A", 3, "+", "KEyK5s3pcKjE", 0, 0),
        ("1", 299, 300, "m6A", 4, "-", "KEyK5s3pcKjE", 0, 0),
        ("1", 599, 600, "m6A", 5, "+", "KEyK5s3pcKjE", 0, 0),
    ]
    b = [
        ("1", 1, 2, "m6A", 6, "+", "FCfhtbEJpbvR", 0, 0),
        ("1", 199, 200, "m6A", 7, "+", "FCfhtbEJpbvR", 0, 0),
        ("1", 299, 300, "m6A", 8, "+", "FCfhtbEJpbvR", 0, 0),
    ]
    c = [
        ("1", 97, 102, "m6A", 9, "+", "3HsmkimcHAFA", 0, 0),
        ("1", 197, 202, "m6A", 10, "+", "3HsmkimcHAFA", 0, 0),
        ("1", 295, 300, "m6A", 11, "-", "3HsmkimcHAFA", 0, 0),
        ("1", 1, 6, "m6A", 12, "+", "3HsmkimcHAFA", 0, 0),
    ]
    # pybedtools defaults score to str, as well as all other fields beyond BED6
    intersect = [
        (
            "1",
            101,
            102,
            "m6A",
            "1",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "97",
            "102",
            "m6A",
            "9",
            "+",
            "3HsmkimcHAFA",
            "0",
            "0",
        ),
        (
            "1",
            199,
            200,
            "m6A",
            "2",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "199",
            "200",
            "m6A",
            "7",
            "+",
            "FCfhtbEJpbvR",
            "0",
            "0",
        ),
        (
            "1",
            199,
            200,
            "m6A",
            "2",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "197",
            "202",
            "m6A",
            "10",
            "+",
            "3HsmkimcHAFA",
            "0",
            "0",
        ),
        (
            "1",
            200,
            201,
            "m6A",
            "3",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "197",
            "202",
            "m6A",
            "10",
            "+",
            "3HsmkimcHAFA",
            "0",
            "0",
        ),
        (
            "1",
            299,
            300,
            "m6A",
            "4",
            "-",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "295",
            "300",
            "m6A",
            "11",
            "-",
            "3HsmkimcHAFA",
            "0",
            "0",
        ),
    ]
    closest = [
        (
            "1",
            101,
            102,
            "m6A",
            "1",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "1",
            "6",
            "m6A",
            "12",
            "+",
            "3HsmkimcHAFA",
            "0",
            "0",
            "-96",
        ),
        (
            "1",
            101,
            102,
            "m6A",
            "1",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "197",
            "202",
            "m6A",
            "10",
            "+",
            "3HsmkimcHAFA",
            "0",
            "0",
            "96",
        ),
        (
            "1",
            199,
            200,
            "m6A",
            "2",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "97",
            "102",
            "m6A",
            "9",
            "+",
            "3HsmkimcHAFA",
            "0",
            "0",
            "-98",
        ),
        (
            "1",
            200,
            201,
            "m6A",
            "3",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "199",
            "200",
            "m6A",
            "7",
            "+",
            "FCfhtbEJpbvR",
            "0",
            "0",
            "-1",
        ),
        (
            "1",
            599,
            600,
            "m6A",
            "5",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "299",
            "300",
            "m6A",
            "8",
            "+",
            "FCfhtbEJpbvR",
            "0",
            "0",
            "-300",
        ),
    ]
    subtract = [("1", "599", "600", "m6A", "5", "+", "KEyK5s3pcKjE", "0", "0")]

    expected = (
        intersect
        if operation == "intersect"
        else closest
        if operation == "closest"
        else subtract
    )

    return a, [b, c], expected


def _get_annotation_file():
    # from io import StringIO

    string = """2\tsource\tgene\t15918350\t15942249\t.\t-\t.\tgene_id "ENSG1"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\ttranscript\t15918350\t15941248\t.\t-\t.\tgene_id "ENSG1"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\texon\t15940974\t15941248\t.\t-\t.\tgene_id "ENSG1"; exon_number "1"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\texon\t15922021\t15922190\t.\t-\t.\tgene_id "ENSG1"; exon_number "2"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\texon\t15918350\t15921122\t.\t-\t.\tgene_id "ENSG1"; exon_number "3"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\ttranscript\t15936265\t15941582\t.\t-\t.\tgene_id "ENSG1"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\texon\t15941532\t15941582\t.\t-\t.\tgene_id "ENSG1"; exon_number "1"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\texon\t15940974\t15941097\t.\t-\t.\tgene_id "ENSG1"; exon_number "2"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\texon\t15938500\t15938725\t.\t-\t.\tgene_id "ENSG1"; exon_number "3"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\texon\t15936265\t15937176\t.\t-\t.\tgene_id "ENSG1"; exon_number "4"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\ttranscript\t15939894\t15942227\t.\t-\t.\tgene_id "ENSG1"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\texon\t15942140\t15942227\t.\t-\t.\tgene_id "ENSG1"; exon_number "1"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\texon\t15940974\t15941309\t.\t-\t.\tgene_id "ENSG1"; exon_number "2"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\texon\t15939894\t15940351\t.\t-\t.\tgene_id "ENSG1"; exon_number "3"; gene_name "A"; gene_biotype "lncRNA";
    2\tsource\tgene\t15940550\t15947007\t.\t+\t.\tgene_id "ENSG2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\ttranscript\t15940550\t15947004\t.\t+\t.\tgene_id "ENSG2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\texon\t15940550\t15940743\t.\t+\t.\tgene_id "ENSG2"; exon_number "1"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\texon\t15941948\t15942854\t.\t+\t.\tgene_id "ENSG2"; exon_number "2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\tCDS\t15942065\t15942854\t.\t+\t0\tgene_id "ENSG2"; exon_number "2"; gene_name "B";  gene_biotype "protein_coding";
    2\tsource\tstart_codon\t15942065\t15942067\t.\t+\t0\tgene_id "ENSG2"; exon_number "2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\texon\t15945493\t15947004\t.\t+\t.\tgene_id "ENSG2"; exon_number "3"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\tCDS\t15945493\t15946094\t.\t+\t2\tgene_id "ENSG2"; exon_number "3"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\tstop_codon\t15946095\t15946097\t.\t+\t0\tgene_id "ENSG2";   exon_number "3"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\tfive_prime_utr\t15940550\t15940743\t.\t+\t.\tgene_id "ENSG2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\tfive_prime_utr\t15941948\t15942064\t.\t+\t.\tgene_id "ENSG2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\tthree_prime_utr\t15946098\t15947004\t.\t+\t.\tgene_id "ENSG2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\ttranscript\t15940566\t15947007\t.\t+\t.\tgene_id "ENSG2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\texon\t15940566\t15940743\t.\t+\t.\tgene_id "ENSG2"; exon_number "1"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\tCDS\t15940587\t15940743\t.\t+\t0\tgene_id "ENSG2"; exon_number "1"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\tstart_codon\t15940587\t15940589\t.\t+\t0\tgene_id "ENSG2"; exon_number "1"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\texon\t15945493\t15947007\t.\t+\t.\tgene_id "ENSG2"; exon_number "2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\tCDS\t15945493\t15946094\t.\t+\t2\tgene_id "ENSG2"; exon_number "2"; gene_name "B";  gene_biotype "protein_coding";
    2\tsource\tstop_codon\t15946095\t15946097\t.\t+\t0\tgene_id "ENSG2"; exon_number "2"; gene_name "B";  gene_biotype "protein_coding";
    2\tsource\tfive_prime_utr\t15940566\t15940586\t.\t+\t.\tgene_id "ENSG2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\tthree_prime_utr\t15946098\t15947007\t.\t+\t.\tgene_id "ENSG2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\ttranscript\t15943557\t15946539\t.\t+\t.\tgene_id "ENSG2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\texon\t15943557\t15943695\t.\t+\t.\tgene_id "ENSG2"; exon_number "1"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\texon\t15945493\t15946539\t.\t+\t.\tgene_id "ENSG2"; exon_number "2"; gene_name "B"; gene_biotype "protein_coding";
    2\tsource\tgene\t15943560\t15943690\t.\t+\t.\tgene_id "ENSG3"; gene_name "C"; gene_biotype "protein_coding";
    2\tsource\ttranscript\t15943560\t15943690\t.\t+\t.\tgene_id "ENSG3"; gene_name "C"; gene_biotype "protein_coding";
    2\tsource\texon\t15943560\t15943690\t.\t+\t.\tgene_id "ENSG3"; exon_number "1"; gene_name "C"; gene_biotype "protein_coding";"""
    # return StringIO(string)
    return string


@pytest.mark.parametrize(
    "operation",
    [
        ("intersect"),
        ("closest"),
        ("subtract"),
    ],
)
def test_get_intersect(operation):
    a_records, b_records, expected_records = _get_records(operation)
    records = get_op(operation)(a_records, b_records)

    assert records == expected_records


# def test_get_annotation():
#     records = [
#         ("2", 15940573, 15940574, "m6A", 1, "+"),
#         ("2", 15940606, 15940607, "m6A", 2, "+"),
#         ("2", 15942303, 15942304, "m6A", 3, "+"),
#         ("2", 15943582, 15943583, "m6A", 4, "+"),
#         ("2", 15946237, 15946238, "m6A", 5, "+"),
#         ("2", 15940993, 15940994, "m6A", 6, "+"),
#         ("2", 15940994, 15940995, "m6A", 7, "-"),
#         ("2", 15941742, 15941743, "m6A", 8, "+"),
#         ("2", 15942160, 15942161, "m6A", 9, "+"),
#         ("2", 15942161, 15942162, "m6A", 10, "-"),
#     ]

#     expected_annotated = [
#         ("1", "1", "Exon", "B", "ENSG2", "protein_coding"),
#         ("1", "1", "5'UTR", "B", "ENSG2", "protein_coding"),
#         ("2", "1", "Exon", "B", "ENSG2", "protein_coding"),
#         ("2", "1", "5'UTR", "B", "ENSG2", "protein_coding"),
#         ("2", "1", "CDS", "B", "ENSG2", "protein_coding"),
#         ("3", "1", "CDS", "B", "ENSG2", "protein_coding"),
#         ("3", "1", "Exon", "B", "ENSG2", "protein_coding"),
#         ("4", "1", "Exon", None, None, "protein_coding"),
#         ("5", "1", "Exon", "B", "ENSG2", "protein_coding"),
#         ("5", "1", "3'UTR", "B", "ENSG2", "protein_coding"),
#         ("6", "1", "Intron", "B", "ENSG2", "protein_coding"),
#         ("7", "1", "Exon", "A", "ENSG1", "lncRNA"),
#         ("8", "1", "Intron", "B", "ENSG2", "protein_coding"),
#         ("9", "1", "Exon", "B", "ENSG2", "protein_coding"),
#         ("9", "1", "CDS", "B", "ENSG2", "protein_coding"),
#         ("10", "1", "Exon", "A", "ENSG1", "lncRNA"),
#     ]

#     annotation_file = _get_annotation_file()
#     annotation_iterable = [
#         tuple(i.strip().split("\t")) for i in annotation_file.splitlines()
#     ]
#     annotation_id = 1

#     with tempfile.TemporaryDirectory(dir="/tmp/") as tempdir:
#         chrom_file = Path(tempdir, "chrom.sizes")
#         string = "2\t242193529\n"
#         with open(chrom_file, "w") as f:
#             f.write(string)

#         annotated = get_genomic_annotation(
#             annotation_iterable, chrom_file, annotation_id, records
#         )
#         assert set(annotated) == set(expected_annotated)

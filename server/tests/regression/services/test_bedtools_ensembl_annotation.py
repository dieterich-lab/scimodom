from pathlib import Path
import filecmp

import pytest

from scimodom.database.models import Data
from scimodom.services.bedtools import BedToolsService
from scimodom.services.annotation.ensembl import EnsemblAnnotationService
from scimodom.utils.dtos.bedtools import (
    GenomicAnnotationRecord,
    DataAnnotationRecord,
    Bed6Record,
)
from scimodom.utils.specs.enums import Strand

# NOTE: subject to change cf. #119

DATA_DIR = Path(Path(__file__).parents[1], "data")
FEATURES = EnsemblAnnotationService.FEATURES

RECORDS = [
    Data(
        id=1,
        dataset_id=1,
        modification_id=1,
        chrom="1",
        start=20652450,
        end=20652451,
        name="m5C",
        score=0,
        strand=Strand.REVERSE,
        thick_start=20652450,
        thick_end=20652451,
        item_rgb="0,0,0",
        coverage=0,
        frequency=1,
    ),
    Data(
        id=2,
        dataset_id=1,
        modification_id=1,
        chrom="1",
        start=236484340,
        end=236484341,
        name="m5C",
        score=0,
        strand=Strand.FORWARD,
        thick_start=236484340,
        thick_end=236484341,
        item_rgb="0,0,0",
        coverage=0,
        frequency=1,
    ),
    Data(
        id=3,
        dataset_id=1,
        modification_id=1,
        chrom="10",
        start=87864331,
        end=87864332,
        name="m5C",
        score=0,
        strand=Strand.FORWARD,
        thick_start=87864331,
        thick_end=87864332,
        item_rgb="0,0,0",
        coverage=0,
        frequency=1,
    ),
    Data(
        id=4,
        dataset_id=1,
        modification_id=1,
        chrom="10",
        start=5853735,
        end=5853736,
        name="m5C",
        score=0,
        strand=Strand.REVERSE,
        thick_start=5853735,
        thick_end=5853736,
        item_rgb="0,0,0",
        coverage=0,
        frequency=1,
    ),
    Data(
        id=5,
        dataset_id=1,
        modification_id=1,
        chrom="MT",
        start=13808,
        end=13809,
        name="m5C",
        score=0,
        strand=Strand.FORWARD,
        thick_start=13808,
        thick_end=13809,
        item_rgb="0,0,0",
        coverage=0,
        frequency=1,
    ),
]

EXPECTED_GENOMIC_ANNOTATION_RECORDS = [
    GenomicAnnotationRecord(
        id="ENSG00000000002", annotation_id=1, name="GENE2", biotype="lncRNA"
    ),
    GenomicAnnotationRecord(
        id="ENSG00000000001", annotation_id=1, name="GENE1", biotype="protein_coding"
    ),
    GenomicAnnotationRecord(
        id="ENSG00000000007", annotation_id=1, name="GENE7", biotype="protein_coding"
    ),
    GenomicAnnotationRecord(
        id="ENSG00000000008",
        annotation_id=1,
        name="GENE8",
        biotype="transcribed_processed_pseudogene",
    ),
    GenomicAnnotationRecord(
        id="ENSG00000000004", annotation_id=1, name="GENE4", biotype="protein_coding"
    ),
    GenomicAnnotationRecord(
        id="ENSG00000000003",
        annotation_id=1,
        name="ENSG00000000003",
        biotype="protein_coding",
    ),
    GenomicAnnotationRecord(
        id="ENSG00000000005", annotation_id=1, name="GENE5", biotype="protein_coding"
    ),
    GenomicAnnotationRecord(
        id="ENSG00000000006", annotation_id=1, name="GENE6", biotype="protein_coding"
    ),
    GenomicAnnotationRecord(
        id="ENSIntergenic", annotation_id=1, name=None, biotype=None
    ),
]

EXPECTED_DATA_RECORDS = [
    DataAnnotationRecord(gene_id="ENSG00000000001", data_id=1, feature="Exonic"),
    DataAnnotationRecord(gene_id="ENSG00000000007", data_id=2, feature="Exonic"),
    DataAnnotationRecord(gene_id="ENSG00000000008", data_id=2, feature="Exonic"),
    DataAnnotationRecord(gene_id="ENSG00000000004", data_id=3, feature="Exonic"),
    DataAnnotationRecord(gene_id="ENSG00000000006", data_id=5, feature="Exonic"),
    DataAnnotationRecord(gene_id="ENSG00000000004", data_id=3, feature="5'UTR"),
    DataAnnotationRecord(gene_id="ENSG00000000007", data_id=2, feature="3'UTR"),
    DataAnnotationRecord(gene_id="ENSG00000000001", data_id=1, feature="CDS"),
    DataAnnotationRecord(gene_id="ENSG00000000004", data_id=3, feature="CDS"),
    DataAnnotationRecord(gene_id="ENSG00000000006", data_id=5, feature="CDS"),
    DataAnnotationRecord(gene_id="ENSIntergenic", data_id=4, feature="Intergenic"),
]


@pytest.fixture
def chrom_file(tmp_path):
    file_path = tmp_path / "chrom.sizes"
    with open(file_path, "w") as fh:
        fh.write("1\t248956422\n")
        fh.write("10\t133797422\n")
        fh.write("MT\t16569\n")
    return Path(file_path)


def _get_bedtools_service(tmp_path):
    return BedToolsService(tmp_path=tmp_path)


# tests


@pytest.mark.datafiles(Path(DATA_DIR, "test.gtf.gz"))
def test_get_ensembl_annotation_records(datafiles, tmp_path):
    bedtools_service = _get_bedtools_service(tmp_path)
    records = bedtools_service.get_ensembl_annotation_records(
        Path(datafiles, "test.gtf.gz"), 1, FEATURES["extended"]["intergenic"]
    )
    assert list(records) == EXPECTED_GENOMIC_ANNOTATION_RECORDS


@pytest.mark.datafiles(Path(DATA_DIR, "test.gtf.gz"))
def test_ensembl_to_bed_features(datafiles, tmp_path, chrom_file):
    bedtools_service = _get_bedtools_service(tmp_path)
    bedtools_service.ensembl_to_bed_features(
        Path(datafiles, "test.gtf.gz"), chrom_file, FEATURES
    )
    filecmp.clear_cache()
    features = {k: list(v.keys()) for k, v in FEATURES.items()}
    for feature in [f for l in features.values() for f in l]:
        ff = f"{feature}.bed"
        assert (
            filecmp.cmp(Path(datafiles, ff), Path(DATA_DIR, ff), shallow=False) is True
        )


def test_annotate_data_using_ensembl(tmp_path):
    features = {
        **EnsemblAnnotationService.FEATURES["conventional"],
        **EnsemblAnnotationService.FEATURES["extended"],
    }
    bedtools_service = _get_bedtools_service(tmp_path)
    annotated_records = bedtools_service.annotate_data_using_ensembl(
        DATA_DIR, features, RECORDS
    )
    assert list(annotated_records) == EXPECTED_DATA_RECORDS


@pytest.mark.datafiles(
    Path(DATA_DIR, "test.fa.gz"),
    Path(DATA_DIR, "test.fa.gz.gzi"),
    Path(DATA_DIR, "test.fa.gz.fai"),
)
# what happend with Strand.UNDEFINE ?
@pytest.mark.parametrize(
    "strand,base",
    [
        (Strand.FORWARD, "C"),
        (Strand.REVERSE, "G"),
    ],
)
def test_get_fasta(datafiles, strand, base, tmp_path):
    record = [
        Bed6Record(chrom="1", start=386, end=387, name="m5C", score=0, strand=strand)
    ]
    expected_fasta_lines = [f">1:386-387({strand.value})", base]
    bedtools_service = _get_bedtools_service(tmp_path)
    seq_file = bedtools_service.getfasta(
        record, Path(datafiles, "test.fa.gz"), is_strand=True
    )
    with open(seq_file, "r") as fh:
        for line, expected_line in zip(fh, expected_fasta_lines):
            assert line.strip() == expected_line

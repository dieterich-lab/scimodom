from datetime import datetime, timezone
import gzip
from pathlib import Path

import pytest
from sqlalchemy import select

from scimodom.database.models import (
    Selection,
    Dataset,
    Data,
    Project,
    ProjectContact,
    GenomicAnnotation,
    DataAnnotation,
)
from scimodom.services.annotation import (
    AnnotationService,
    EnsemblAnnotationService,
    AnnotationVersionError,
    InstantiationError,
    AnnotationFormatError,
)
from scimodom.services.importer.base import MissingDataError
from scimodom.utils.operations import write_annotation_to_bed


def test_get_annotation_path(Session, data_path):
    assert AnnotationService.get_annotation_path() == Path(data_path.ANNOTATION_PATH)


def test_get_gene_cache_path(Session, data_path):
    assert AnnotationService.get_cache_path() == Path(
        data_path.LOC, "cache", "gene", "selection"
    )


def test_init_from_id_wrong_id(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    with pytest.raises(InstantiationError) as exc:
        service = AnnotationService(Session(), annotation_id=99)
    assert (str(exc.value)) == "Failed to find annotation 99"
    assert exc.type == InstantiationError


def test_init_from_id_wrong_version(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    with pytest.raises(AnnotationVersionError) as exc:
        service = AnnotationService(Session(), annotation_id=3)
    assert (str(exc.value)) == "Invalid annotation version A8syx5TzWlK0"
    assert exc.type == AnnotationVersionError


def test_init_from_id(Session, setup, data_path):
    # taxid is wrong but does not matter as id has priority
    # annotation file path is available, but file does not yet exists
    with Session() as session, session.begin():
        session.add_all(setup)
    service = AnnotationService(Session(), annotation_id=1, taxa_id=0)
    # annotation_file = service.ANNOTATION_FILE(
    #     organism="Homo_sapiens",
    #     assembly="GRCh38",
    #     release=service._annotation.release,
    #     fmt=service.FMT,
    # )
    assert service._annotation.release == 110
    assert service._annotation.taxa_id == 9606
    # assert service._annotation_file == Path(
    #     data_path.ANNOTATION_PATH,
    #     "Homo_sapiens",
    #     "GRCh38",
    #     str(service._annotation.release),
    #     annotation_file,
    # )
    assert service._chrom_file == Path(
        data_path.ASSEMBLY_PATH, "Homo_sapiens", "GRCh38", "chrom.sizes"
    )


def test_init_no_source(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    with pytest.raises(AssertionError) as exc:
        service = AnnotationService(Session(), taxa_id=9606)
    assert (
        str(exc.value)
        == "Undefined 'None'. Allowed values are typing.Literal['ensembl', 'gtrnadb']."
    )
    assert exc.type == AssertionError


def test_init_from_taxid_fail(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    with pytest.raises(InstantiationError) as exc:
        service = AnnotationService(Session(), taxa_id=0, source="ensembl")
    assert (
        str(exc.value)
        == "Failed to find annotation with taxonomy ID 0 and source ensembl"
    )
    assert exc.type == InstantiationError


# def test_init_from_taxid(Session, setup, data_path):
#     with Session() as session, session.begin():
#         session.add_all(setup)
#     service = AnnotationService(Session(), taxa_id=9606)
#     annotation_file = service.ANNOTATION_FILE(
#         organism="Homo_sapiens",
#         assembly="GRCh38",
#         release=service._release,
#         fmt=service.FMT,
#     )
#     assert service._db_version == "EyRBnPeVwbzW"
#     assert service._annotation_id == 1
#     assert service._release == 110
#     assert service._annotation_file == Path(
#         data_path.ANNOTATION_PATH,
#         "Homo_sapiens",
#         "GRCh38",
#         str(service._release),
#         annotation_file,
#     )
#     assert service._chrom_file == Path(
#         data_path.ASSEMBLY_PATH, "Homo_sapiens", "GRCh38", "chrom.sizes"
#     )


# due to scope of data_path this must be called before the rest...
def test_download_annotation(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = AnnotationService(Session(), annotation_id=1)
    parent = service._annotation_file.parent
    parent.mkdir(parents=True, exist_ok=False)
    service._download()
    # only assert if created
    assert service._annotation_file.is_file()


def test_create_annotation_exists_no_records(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    dest = Path(data_path.ANNOTATION_PATH, "Homo_sapiens", "GRCh38", "110")
    dest.mkdir(parents=True, exist_ok=True)
    with pytest.raises(Exception) as exc:
        service = AnnotationService(Session(), annotation_id=1)
        service.create_annotation()
    assert (
        str(exc.value)
        == f"Annotation directory {dest.as_posix()} already exists... but there is no record in GenomicAnnotation matching the current annotation 1 (9606, 110). Aborting transaction!"
    )


def test_create_annotation_exists(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
        # add random entry in GenomicAnnotation
        annotation = GenomicAnnotation(
            id="ENSG000000000000",
            annotation_id=1,
            name="GENE1",
            biotype="protein_coding",
        )
        session.add(annotation)
        session.commit()
    dest = Path(data_path.ANNOTATION_PATH, "Homo_sapiens", "GRCh38", "110")
    dest.mkdir(parents=True, exist_ok=True)
    service = AnnotationService(Session(), annotation_id=1)
    service.create_annotation()


# this actually relies on "operations.py" and import buffer
def test_create_annotation_records(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = AnnotationService(Session(), annotation_id=1)
    parent = service._annotation_file.parent
    parent.mkdir(parents=True, exist_ok=True)
    gtf = _mock_gtf()
    with gzip.open(service._annotation_file, "wt") as gtf_file:
        gtf_file.write(gtf)
    service._create_annotation()

    expected_records = [
        ("ENSG00000000001", 1, "A", "protein_coding"),
        ("ENSG00000000002", 1, "B", "processed_pseudogene"),
        ("ENSIntergenic", 1, None, None),
    ]
    with Session() as session, session.begin():
        records = session.execute(select(GenomicAnnotation)).scalars().all()
        for row, expected_row in zip(records, expected_records):
            assert row.id == expected_row[0]
            assert row.annotation_id == expected_row[1]
            assert row.name == expected_row[2]
            assert row.biotype == expected_row[3]


# this actually relies on "operations.py", and calls _create_annotation
def test_annotate_records(Session, setup, data_path):
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    with Session() as session, session.begin():
        session.add_all(setup)
        selection = Selection(
            modification_id=1,
            technology_id=1,
            organism_id=1,
        )
        session.add(selection)
        session.flush()
        selection_id = selection.id
        contact = ProjectContact(
            contact_name="contact_name",
            contact_institution="contact_institution",
            contact_email="contact@email",
        )
        session.add(contact)
        session.flush()
        contact_id = contact.id
        project = Project(
            id="12345678",
            title="title",
            summary="summary",
            contact_id=contact_id,
            date_published=datetime.fromisoformat("2024-01-01"),
            date_added=stamp,
        )
        session.add(project)
        session.flush()
        smid = project.id
        dataset = Dataset(
            id="KEyK5s3pcKjE",
            project_id=smid,
            organism_id=1,
            technology_id=1,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        session.add(dataset)
        session.flush()
        eufid = dataset.id
        rows = _get_records()
        data = [
            Data(
                dataset_id=eufid,
                modification_id=1,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows
        ]
        session.add_all(data)
        session.commit()

    service = AnnotationService(Session(), annotation_id=1)
    parent = service._annotation_file.parent
    parent.mkdir(parents=True, exist_ok=True)
    gtf = _mock_gtf()
    with gzip.open(service._annotation_file, "wt") as gtf_file:
        gtf_file.write(gtf)
    parent = service._chrom_file.parent
    parent.mkdir(parents=True, exist_ok=True)
    string = "1\t248956422\n"
    with open(service._chrom_file, "w") as chrom_file:
        chrom_file.write(string)
    features = {k: list(v.keys()) for k, v in service.FEATURES.items()}
    write_annotation_to_bed(
        service._annotation_file, service._chrom_file, features, AnnotationFormatError
    )
    service._create_annotation()
    service.annotate_data(eufid)

    expected_records = [
        (1, 5, "ENSG00000000001", "Exonic"),
        (2, 1, "ENSG00000000001", "Exonic"),
        (3, 2, "ENSG00000000001", "Exonic"),
        (4, 3, "ENSG00000000001", "Exonic"),
        (5, 4, "ENSG00000000002", "Exonic"),
        (6, 5, "ENSG00000000001", "5'UTR"),
        (7, 3, "ENSG00000000001", "3'UTR"),
        (8, 1, "ENSG00000000001", "CDS"),
        (9, 2, "ENSG00000000001", "CDS"),
        (10, 6, "ENSG00000000002", "Intronic"),
        (11, 8, "ENSIntergenic", "Intergenic"),
    ]
    with Session() as session, session.begin():
        records = session.execute(select(DataAnnotation)).scalars().all()
        for row, expected_row in zip(records, expected_records):
            assert row.id == expected_row[0]
            assert row.data_id == expected_row[1]
            assert row.gene_id == expected_row[2]
            assert row.feature == expected_row[3]


# this actually relies on "operations.py", and calls _create_annotation
def test_annotate_records_no_records(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = AnnotationService(Session(), annotation_id=1)
    with pytest.raises(MissingDataError) as exc:
        service.annotate_data("123456789abc")
    assert str(exc.value) == "[Annotation] No records found for 123456789abc... "
    assert exc.type == MissingDataError


def test_update_gene_cache(Session, setup, data_path):
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    with Session() as session, session.begin():
        session.add_all(setup)
        selection = Selection(
            modification_id=1,
            technology_id=1,
            organism_id=1,
        )
        session.add(selection)
        session.flush()
        selection_id = selection.id
        contact = ProjectContact(
            contact_name="contact_name",
            contact_institution="contact_institution",
            contact_email="contact@email",
        )
        session.add(contact)
        session.flush()
        contact_id = contact.id
        project = Project(
            id="12345678",
            title="title",
            summary="summary",
            contact_id=contact_id,
            date_published=datetime.fromisoformat("2024-01-01"),
            date_added=stamp,
        )
        session.add(project)
        session.flush()
        smid = project.id
        dataset = Dataset(
            id="KEyK5s3pcKjE",
            project_id=smid,
            organism_id=1,
            technology_id=1,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        session.add(dataset)
        session.flush()
        eufid = dataset.id
        rows = _get_records()
        data = [
            Data(
                dataset_id=eufid,
                modification_id=1,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows
        ]
        session.add_all(data)
        session.commit()

    service = AnnotationService(Session(), annotation_id=1)
    parent = service._annotation_file.parent
    parent.mkdir(parents=True, exist_ok=True)
    gtf = _mock_gtf()
    with gzip.open(service._annotation_file, "wt") as gtf_file:
        gtf_file.write(gtf)
    parent = service._chrom_file.parent
    parent.mkdir(parents=True, exist_ok=True)
    string = "1\t248956422\n"
    with open(service._chrom_file, "w") as chrom_file:
        chrom_file.write(string)
    features = {k: list(v.keys()) for k, v in service.FEATURES.items()}
    write_annotation_to_bed(
        service._annotation_file, service._chrom_file, features, AnnotationFormatError
    )
    service._create_annotation()
    service.annotate_data(eufid)
    service.update_gene_cache(eufid, {1: 1})
    parent = service.get_gene_cache_path()
    with open(Path(parent, "1"), "r") as f:
        genes = f.read().splitlines()
    assert set(genes) == {"A", "B"}


def _mock_gtf():
    string = """#!genome-build GRCh38
#!genome-version GRCh38
#!genome-date
#!genome-build-accession
#!genebuild-last-updated
1	ensembl_havana	gene	65419	71585	.	+	.	gene_id "ENSG00000000001"; gene_version "7"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding";
1	havana	transcript	65419	71585	.	+	.	gene_id "ENSG00000000001"; gene_version "7"; transcript_id "ENST00000000001"; transcript_version "2"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding"; transcript_name "A-1"; transcript_source "havana"; transcript_biotype "protein_coding"; tag "CCDS"; ccds_id "CCDS00000"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select";
1	havana	exon	65419	65433	.	+	.	gene_id "ENSG00000000001"; gene_version "7"; transcript_id "ENST00000000001"; transcript_version "2"; exon_number "1"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding"; transcript_name "A-1"; transcript_source "havana"; transcript_biotype "protein_coding"; tag "CCDS"; ccds_id "CCDS00001"; exon_id "ENSE00000000001"; exon_version "1"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select";
1	havana	exon	65520	65573	.	+	.	gene_id "ENSG00000000001"; gene_version "7"; transcript_id "ENST00000000001"; transcript_version "2"; exon_number "2"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding"; transcript_name "A-1"; transcript_source "havana"; transcript_biotype "protein_coding"; tag "CCDS"; ccds_id "CCDS00002"; exon_id "ENSE00000000002"; exon_version "1"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select";
1	havana	CDS	65565	65573	.	+	0	gene_id "ENSG00000000001"; gene_version "7"; transcript_id "ENST00000000001"; transcript_version "2"; exon_number "2"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding"; transcript_name "A-1"; transcript_source "havana"; transcript_biotype "protein_coding"; tag "CCDS"; ccds_id "CCDS00003"; protein_id "ENSP00000493376"; protein_version "2"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select";
1	havana	start_codon	65565	65567	.	+	0	gene_id "ENSG00000000001"; gene_version "7"; transcript_id "ENST00000000001"; transcript_version "2"; exon_number "2"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding"; transcript_name "A-1"; transcript_source "havana"; transcript_biotype "protein_coding"; tag "CCDS"; ccds_id "CCDS00004"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select";
1	havana	exon	69037	71585	.	+	.	gene_id "ENSG00000000001"; gene_version "7"; transcript_id "ENST00000000001"; transcript_version "2"; exon_number "3"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding"; transcript_name "A-1"; transcript_source "havana"; transcript_biotype "protein_coding"; tag "CCDS"; ccds_id "CCDS00005"; exon_id "ENSE00000000003"; exon_version "1"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select";
1	havana	CDS	69037	70005	.	+	0	gene_id "ENSG00000000001"; gene_version "7"; transcript_id "ENST00000000001"; transcript_version "2"; exon_number "3"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding"; transcript_name "A-1"; transcript_source "havana"; transcript_biotype "protein_coding"; tag "CCDS"; ccds_id "CCDS00006"; protein_id "ENSP00000493376"; protein_version "2"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select";
1	havana	stop_codon	70006	70008	.	+	0	gene_id "ENSG00000000001"; gene_version "7"; transcript_id "ENST00000000001"; transcript_version "2"; exon_number "3"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding"; transcript_name "A-1"; transcript_source "havana"; transcript_biotype "protein_coding"; tag "CCDS"; ccds_id "CCDS00007"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select";
1	havana	five_prime_utr	65419	65433	.	+	.	gene_id "ENSG00000000001"; gene_version "7"; transcript_id "ENST00000000001"; transcript_version "2"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding"; transcript_name "A-1"; transcript_source "havana"; transcript_biotype "protein_coding"; tag "CCDS"; ccds_id "CCDS00008"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select";
1	havana	five_prime_utr	65520	65564	.	+	.	gene_id "ENSG00000000001"; gene_version "7"; transcript_id "ENST00000000001"; transcript_version "2"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding"; transcript_name "A-1"; transcript_source "havana"; transcript_biotype "protein_coding"; tag "CCDS"; ccds_id "CCDS00009"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select";
1	havana	three_prime_utr	70009	71585	.	+	.	gene_id "ENSG00000000001"; gene_version "7"; transcript_id "ENST00000000001"; transcript_version "2"; gene_name "A"; gene_source "ensembl_havana"; gene_biotype "protein_coding"; transcript_name "A-1"; transcript_source "havana"; transcript_biotype "protein_coding"; tag "CCDS"; ccds_id "CCDS00010"; tag "basic"; tag "Ensembl_canonical"; tag "MANE_Select";
1	havana	gene	487101	489906	.	+	.	gene_id "ENSG00000000002"; gene_version "3"; gene_name "B"; gene_source "havana"; gene_biotype "processed_pseudogene";
1	havana	transcript	487101	489906	.	+	.	gene_id "ENSG00000000002"; gene_version "3"; transcript_id "ENST00000000002"; transcript_version "3"; gene_name "B"; gene_source "havana"; gene_biotype "processed_pseudogene"; transcript_name "B-1"; transcript_source "havana"; transcript_biotype "processed_pseudogene"; tag "basic"; tag "Ensembl_canonical"; transcript_support_level "NA";
1	havana	exon	487101	489387	.	+	.	gene_id "ENSG00000000002"; gene_version "3"; transcript_id "ENST00000000002"; transcript_version "3"; exon_number "1"; gene_name "B"; gene_source "havana"; gene_biotype "processed_pseudogene"; transcript_name "B-1"; transcript_source "havana"; transcript_biotype "processed_pseudogene"; exon_id "ENSE00000000001"; exon_version "3"; tag "basic"; tag "Ensembl_canonical"; transcript_support_level "NA";
1	havana	exon	489717	489906	.	+	.	gene_id "ENSG00000000002"; gene_version "3"; transcript_id "ENST00000000002"; transcript_version "3"; exon_number "2"; gene_name "B"; gene_source "havana"; gene_biotype "processed_pseudogene"; transcript_name "B-1"; transcript_source "havana"; transcript_biotype "processed_pseudogene"; exon_id "ENSE00000000002"; exon_version "1"; tag "basic"; tag "Ensembl_canonical"; transcript_support_level "NA";"""
    return string


def _get_records():
    records = [
        ("1", 65570, 65571, "m6A", 1, "+", 65570, 65571, "0,0,0", 10, 20),
        ("1", 70000, 70001, "m6A", 2, "+", 70000, 70001, "0,0,0", 30, 40),
        ("1", 71000, 71001, "m6A", 3, "+", 71000, 71001, "0,0,0", 50, 60),
        ("1", 487100, 487101, "m6A", 4, "+", 487100, 487101, "0,0,0", 70, 80),
        ("1", 65550, 65551, "m6A", 5, "+", 65550, 65551, "0,0,0", 90, 100),
        ("1", 489400, 489401, "m6A", 6, "+", 489400, 489401, "0,0,0", 100, 100),
        ("1", 489700, 489701, "m6A", 7, "-", 489700, 489701, "0,0,0", 100, 100),
        ("1", 487050, 487051, "m6A", 8, "+", 487050, 487051, "0,0,0", 100, 100),
    ]
    return records

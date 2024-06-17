from dataclasses import dataclass
from pathlib import Path
from posixpath import join as urljoin
from typing import Generator, Any, Callable

import pytest
from sqlalchemy.orm import sessionmaker

import scimodom.utils.specifications as specs
from scimodom.database.models import (
    Annotation,
    AnnotationVersion,
    GenomicAnnotation,
    Taxa,
    Taxonomy,
)
from scimodom.services.annotation import (
    EnsemblAnnotationService,
    AnnotationNotFoundError,
)


class MockAssemblyService:
    def __init__(self):
        pass

    def get_name_for_version(self, taxa_id: int) -> str:
        if taxa_id == 9606:
            return "GRCh38"
        else:
            return "GRCm38"

    def get_chrom_file(self, taxa_id):
        pass

    def get_seqids(self, taxa_id):
        pass


class MockDataService:
    def __init__(self):
        pass

    def get_modification_by_dataset(self, datasets):
        pass


class MockBedToolsService:
    def __init__(self):  # noqa
        pass

    def ensembl_to_bed_features(self, annotation_path, chrom_file, features):
        pass

    def annotate_data_using_ensembl(self, annotation_path, features, records):
        pass

    def get_ensembl_annotation_records(
        self, annotation_path, annotation_id, intergenic_feature
    ):
        pass

    def gtrnadb_to_bed_features(self, annotation_path, features):
        pass

    def get_gtrnadb_annotation_records(self, annotation_path, annotation_id, organism):
        pass


class MockExternalService:
    def __init__(self):  # noqa
        pass

    def get_sprinzl_mapping(self, model_file, fasta_file, sprinzl_file):
        return Path(Path(fasta_file).parent, "seq_to_sprinzl.tab").as_posix()


@dataclass
class MockDependencies:
    Session: Callable[[], Generator[sessionmaker, Any, None]]
    assembly_service: MockAssemblyService
    data_service: MockDataService
    bedtools_service: MockBedToolsService
    external_service: MockExternalService


@pytest.fixture
def dependencies(Session, data_path) -> MockDependencies:  # noqa
    yield MockDependencies(
        Session=Session,
        assembly_service=MockAssemblyService(),
        data_service=MockDataService(),
        bedtools_service=MockBedToolsService(),
        external_service=MockExternalService(),
    )


def _get_ensembl_annotation_service(dependencies):
    return EnsemblAnnotationService(
        dependencies.Session(),
        assembly_service=dependencies.assembly_service,
        data_service=dependencies.data_service,
        bedtools_service=dependencies.bedtools_service,
        external_service=dependencies.external_service,
    )


# tests


def test_get_annotation_path(data_path):
    assert EnsemblAnnotationService.get_annotation_path() == Path(
        data_path.ANNOTATION_PATH
    )


def test_get_gene_cache_path(data_path):
    assert EnsemblAnnotationService.get_cache_path() == Path(
        data_path.LOC, "cache", "gene", "selection"
    )


def test_init(dependencies):
    with dependencies.Session() as session, session.begin():
        session.add(AnnotationVersion(version_num="EyRBnPeVwbzW"))
    service = _get_ensembl_annotation_service(dependencies)
    assert service._version == "EyRBnPeVwbzW"


def test_get_annotation(dependencies):
    with dependencies.Session() as session, session.begin():
        version = AnnotationVersion(version_num="EyRBnPeVwbzW")
        taxonomy = Taxonomy(
            id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
        )
        taxa = Taxa(
            id=9606,
            name="Homo sapiens",
            short_name="H. sapiens",
            taxonomy_id="a1b240af",
        )
        annotation = Annotation(
            release=110, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"
        )
        session.add_all([version, taxonomy, taxa, annotation])
    service = _get_ensembl_annotation_service(dependencies)
    annotation = service.get_annotation(9606)
    assert annotation.release == 110
    assert annotation.taxa_id == 9606
    assert annotation.source == "ensembl"
    assert annotation.version == "EyRBnPeVwbzW"


def test_get_annotation_fail(dependencies):
    with dependencies.Session() as session, session.begin():
        session.add(AnnotationVersion(version_num="EyRBnPeVwbzW"))
    service = _get_ensembl_annotation_service(dependencies)
    with pytest.raises(AnnotationNotFoundError) as exc:
        service.get_annotation(9606)
    assert (str(exc.value)) == "No such ensembl annotation for taxonomy ID: 9606."
    assert exc.type == AnnotationNotFoundError


def test_get_release_path(dependencies, data_path):
    with dependencies.Session() as session, session.begin():
        version = AnnotationVersion(version_num="EyRBnPeVwbzW")
        taxonomy = Taxonomy(
            id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
        )
        taxa = Taxa(
            id=9606,
            name="Homo sapiens",
            short_name="H. sapiens",
            taxonomy_id="a1b240af",
        )
        annotation = Annotation(
            release=110, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"
        )
        session.add_all([version, taxonomy, taxa, annotation])
    service = _get_ensembl_annotation_service(dependencies)
    annotation = service.get_annotation(9606)
    release_path = service.get_release_path(annotation)
    expected_release_path = Path(
        data_path.ANNOTATION_PATH, "Homo_sapiens", "GRCh38", "110"
    )
    assert release_path == expected_release_path


def test_release_exists(dependencies):
    with dependencies.Session() as session, session.begin():
        version = AnnotationVersion(version_num="EyRBnPeVwbzW")
        taxonomy = Taxonomy(
            id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
        )
        taxa = Taxa(
            id=9606,
            name="Homo sapiens",
            short_name="H. sapiens",
            taxonomy_id="a1b240af",
        )
        annotation = Annotation(
            release=110, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"
        )
        genomic_annotation = GenomicAnnotation(
            id="ENSG00000000001", annotation_id=1, name="A", biotype="protein_coding"
        )
        session.add_all([version, taxonomy, taxa, annotation, genomic_annotation])
    service = _get_ensembl_annotation_service(dependencies)
    annotation = service.get_annotation(9606)
    assert service._release_exists(annotation.id)


# def test_download(data_path):
#     test_release_path = Path(data_path.ANNOTATION_PATH, "Homo_sapiens", "GRCh38", "110")
#     test_release_path.mkdir(parents=True, exist_ok=False)
#     test_file_name = "README.md"
#     test_url = urljoin(
#         "https://github.com/dieterich-lab",
#         "scimodom",
#         "blob",
#         "0f977c262e173d4ce5668fda6b6b73308d275ae5",
#         test_file_name,
#     )
#     test_file = Path(test_release_path, test_file_name)
#     AnnotationService.download(test_url, test_file)
#     assert test_file.is_file()


# Ensembl


def test_ensembl_annotation_paths(data_path, dependencies):
    with dependencies.Session() as session, session.begin():
        version = AnnotationVersion(version_num="EyRBnPeVwbzW")
        taxonomy = Taxonomy(
            id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
        )
        taxa = Taxa(
            id=9606,
            name="Homo sapiens",
            short_name="H. sapiens",
            taxonomy_id="a1b240af",
        )
        annotation = Annotation(
            release=110, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"
        )
        session.add_all([version, taxonomy, taxa, annotation])
    service = _get_ensembl_annotation_service(dependencies)
    annotation = service.get_annotation(9606)
    release_path = service.get_release_path(annotation)
    annotation_file, url = service._get_annotation_paths(annotation, release_path)
    expected_annotation_file = service.ANNOTATION_FILE(
        organism="Homo_sapiens", assembly="GRCh38", release="110", fmt="gtf"
    )
    expected_annotation_path = Path(
        data_path.ANNOTATION_PATH,
        "Homo_sapiens",
        "GRCh38",
        "110",
        expected_annotation_file,
    )
    expected_url = urljoin(
        specs.ENSEMBL_FTP,
        "release-110",
        "gtf",
        "homo_sapiens",
        expected_annotation_file,
    )
    assert annotation_file == expected_annotation_path
    assert url == expected_url


# def test_ensembl_update_database(setup, data_path, dependencies):
#     with dependencies.Session() as session, session.begin():
#         session.add_all(setup)
#     service = _get_ensembl_annotation_service(dependencies)
#     annotation_path, _ = service._get_annotation_paths()
#     service._release_path.mkdir(parents=True, exist_ok=True)
#     gtf = _mock_gtf()
#     with gzip.open(annotation_path, "wt") as gtf_file:
#         gtf_file.write(gtf)
#     service._update_database(annotation_path)

#     expected_records = [
#         ("ENSG00000000001", 1, "A", "protein_coding"),
#         ("ENSG00000000002", 1, "B", "processed_pseudogene"),
#         ("ENSIntergenic", 1, None, None),
#     ]
#     with _annotation_setup.Session() as session, session.begin():
#         records = session.execute(select(GenomicAnnotation)).scalars().all()
#         for row, expected_row in zip(records, expected_records):
#             assert row.id == expected_row[0]
#             assert row.annotation_id == expected_row[1]
#             assert row.name == expected_row[2]
#             assert row.biotype == expected_row[3]


# def test_ensembl_annotate_data(setup, data_path, _annotation_setup):
#     stamp = datetime.now(timezone.utc).replace(microsecond=0)
#     with _annotation_setup.Session() as session, session.begin():
#         session.add_all(setup)
#         selection = Selection(
#             modification_id=1,
#             technology_id=1,
#             organism_id=1,
#         )
#         session.add(selection)
#         session.flush()
#         selection_id = selection.id
#         contact = ProjectContact(
#             contact_name="contact_name",
#             contact_institution="contact_institution",
#             contact_email="contact@email",
#         )
#         session.add(contact)
#         session.flush()
#         contact_id = contact.id
#         project = Project(
#             id="12345678",
#             title="title",
#             summary="summary",
#             contact_id=contact_id,
#             date_published=datetime.fromisoformat("2024-01-01"),
#             date_added=stamp,
#         )
#         session.add(project)
#         session.flush()
#         smid = project.id
#         dataset = Dataset(
#             id="KEyK5s3pcKjE",
#             project_id=smid,
#             organism_id=1,
#             technology_id=1,
#             title="title",
#             modification_type="RNA",
#             date_added=stamp,
#         )
#         session.add(dataset)
#         session.flush()
#         eufid = dataset.id
#         rows = _get_records()
#         data = [
#             Data(
#                 dataset_id=eufid,
#                 modification_id=1,
#                 chrom=chrom,
#                 start=start,
#                 end=end,
#                 name=name,
#                 score=score,
#                 strand=strand,
#                 thick_start=thick_start,
#                 thick_end=thick_end,
#                 item_rgb=item_rgb,
#                 coverage=coverage,
#                 frequency=frequency,
#             )
#             for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows
#         ]
#         session.add_all(data)
#         session.commit()

#     service = _get_ensembl_annotation_service(_annotation_setup, annotation_id=1)
#     service._release_path.mkdir(parents=True, exist_ok=True)
#     annotation_path, _ = service._get_annotation_paths()
#     gtf = _mock_gtf()
#     with gzip.open(annotation_path, "wt") as gtf_file:
#         gtf_file.write(gtf)
#     parent = service._chrom_file.parent
#     parent.mkdir(parents=True, exist_ok=True)
#     string = "1\t248956422\n"
#     with open(service._chrom_file, "w") as chrom_file:
#         chrom_file.write(string)
#     features = {k: list(v.keys()) for k, v in service.FEATURES.items()}
#     _annotation_setup.bedtools_service.ensembl_to_bed_features(
#         annotation_path, service._chrom_file, features
#     )
#     service._update_database(annotation_path)
#     service.annotate_data(eufid)

#     expected_records = [
#         (1, 5, "ENSG00000000001", "Exonic"),
#         (2, 1, "ENSG00000000001", "Exonic"),
#         (3, 2, "ENSG00000000001", "Exonic"),
#         (4, 3, "ENSG00000000001", "Exonic"),
#         (5, 4, "ENSG00000000002", "Exonic"),
#         (6, 5, "ENSG00000000001", "5'UTR"),
#         (7, 3, "ENSG00000000001", "3'UTR"),
#         (8, 1, "ENSG00000000001", "CDS"),
#         (9, 2, "ENSG00000000001", "CDS"),
#         (10, 6, "ENSG00000000002", "Intronic"),
#         (11, 8, "ENSIntergenic", "Intergenic"),
#     ]
#     with _annotation_setup.Session() as session, session.begin():
#         records = session.execute(select(DataAnnotation)).scalars().all()
#         for row, expected_row in zip(records, expected_records):
#             assert row.id == expected_row[0]
#             assert row.data_id == expected_row[1]
#             assert row.gene_id == expected_row[2]
#             assert row.feature == expected_row[3]


# error handled eslewhere
# def test_ensembl_annotate_no_data(setup, data_path, _annotation_setup):
#     with _annotation_setup.Session() as session, session.begin():
#         session.add_all(setup)
#     service = _get_ensembl_annotation_service(_annotation_setup, annotation_id=1)
#     with pytest.raises(MissingDataError) as exc:
#         service.annotate_data("123456789abc")
#     assert str(exc.value) == "No records found for 123456789abc"
#     assert exc.type == MissingDataError


# # tested using ensembl
# def test_update_gene_cache(setup, data_path, _annotation_setup):
#     stamp = datetime.now(timezone.utc).replace(microsecond=0)
#     with _annotation_setup.Session() as session, session.begin():
#         session.add_all(setup)
#         selection = Selection(
#             modification_id=1,
#             technology_id=1,
#             organism_id=1,
#         )
#         session.add(selection)
#         session.flush()
#         selection_id = selection.id
#         contact = ProjectContact(
#             contact_name="contact_name",
#             contact_institution="contact_institution",
#             contact_email="contact@email",
#         )
#         session.add(contact)
#         session.flush()
#         contact_id = contact.id
#         project = Project(
#             id="12345678",
#             title="title",
#             summary="summary",
#             contact_id=contact_id,
#             date_published=datetime.fromisoformat("2024-01-01"),
#             date_added=stamp,
#         )
#         session.add(project)
#         session.flush()
#         smid = project.id
#         dataset = Dataset(
#             id="KEyK5s3pcKjE",
#             project_id=smid,
#             organism_id=1,
#             technology_id=1,
#             title="title",
#             modification_type="RNA",
#             date_added=stamp,
#         )
#         session.add(dataset)
#         session.flush()
#         eufid = dataset.id
#         rows = _get_records()
#         data = [
#             Data(
#                 dataset_id=eufid,
#                 modification_id=1,
#                 chrom=chrom,
#                 start=start,
#                 end=end,
#                 name=name,
#                 score=score,
#                 strand=strand,
#                 thick_start=thick_start,
#                 thick_end=thick_end,
#                 item_rgb=item_rgb,
#                 coverage=coverage,
#                 frequency=frequency,
#             )
#             for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows
#         ]
#         session.add_all(data)
#         session.commit()

#     service = _get_ensembl_annotation_service(_annotation_setup, annotation_id=1)
#     annotation_path, _ = service._get_annotation_paths()
#     service._release_path.mkdir(parents=True, exist_ok=True)
#     gtf = _mock_gtf()
#     with gzip.open(annotation_path, "wt") as gtf_file:
#         gtf_file.write(gtf)
#     service._chrom_file.parent.mkdir(parents=True, exist_ok=True)
#     string = "1\t248956422\n"
#     with open(service._chrom_file, "w") as chrom_file:
#         chrom_file.write(string)
#     features = {k: list(v.keys()) for k, v in service.FEATURES.items()}
#     _annotation_setup.bedtools_service.ensembl_to_bed_features(
#         annotation_path, service._chrom_file, features
#     )
#     service._update_database(annotation_path)
#     service.annotate_data(eufid)
#     service.update_gene_cache(eufid, {1: 1})
#     parent = service.get_cache_path()
#     with open(Path(parent, "1"), "r") as f:
#         genes = f.read().splitlines()
#     assert set(genes) == {"A", "B"}


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

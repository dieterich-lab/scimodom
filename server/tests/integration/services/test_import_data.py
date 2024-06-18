from datetime import datetime, timezone
from io import StringIO

import pytest
from sqlalchemy import select

from scimodom.database.models import (
    RNAType,
    Modomics,
    Taxonomy,
    Taxa,
    Assembly,
    AssemblyVersion,
    Annotation,
    AnnotationVersion,
    DetectionMethod,
    DatasetModificationAssociation,
    Selection,
    Dataset,
    Modification,
    DetectionTechnology,
    Organism,
    Project,
    ProjectSource,
    ProjectContact,
    GenomicAnnotation,
)
from scimodom.services.dataset import DatasetService
from scimodom.services.assembly import AssemblyService
from scimodom.services.annotation import AnnotationService, AnnotationSource
from scimodom.services.annotation.ensembl import EnsemblAnnotationService
from scimodom.services.annotation.gtrnadb import GtRNAdbAnnotationService
from scimodom.services.bedtools import BedToolsService
from scimodom.services.data import DataService
from scimodom.services.external import ExternalService
from scimodom.services.file import FileService
from scimodom.services.project import ProjectService
import scimodom.utils.utils as utils


def _add_setup(session):
    rna_type = RNAType(id="WTS", name="Whole transcriptome")
    modomics = Modomics(
        id="2000000006A",
        name="N6-methyladenosine",
        short_name="m6A",
        moiety="nucleoside",
    )
    taxonomy = Taxonomy(
        id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
    )
    taxa = Taxa(
        id=9606, name="Homo sapiens", short_name="H. sapiens", taxonomy_id="a1b240af"
    )
    assembly_version = AssemblyVersion(version_num="GcatSmFcytpU")
    assembly = Assembly(
        name="GRCh38", alt_name="hg38", taxa_id=9606, version="GcatSmFcytpU"
    )
    annotation_version = AnnotationVersion(version_num="EyRBnPeVwbzW")
    annotation = Annotation(
        release=110, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"
    )
    method = DetectionMethod(
        id="91b145ea", cls="NGS 2nd generation", meth="Antibody-based sequencing"
    )
    session.add_all(
        [
            rna_type,
            modomics,
            taxonomy,
            taxa,
            assembly_version,
            assembly,
            annotation_version,
            annotation,
            method,
        ]
    )
    session.flush()


def _add_selection(session):
    modification = Modification(rna="WTS", modomics_id="2000000006A")
    technology = DetectionTechnology(tech="Technology 1", method_id="91b145ea")
    organism = Organism(cto="Cell type 1", taxa_id=9606)
    session.add_all([modification, organism, technology])
    session.flush()
    selection = Selection(
        modification_id=modification.id,
        organism_id=organism.id,
        technology_id=technology.id,
    )
    session.add(selection)
    session.flush()


def _add_contact(session):
    contact = ProjectContact(
        contact_name="Contact Name",
        contact_institution="Contact Institution",
        contact_email="Contact Email",
    )
    session.add(contact)
    session.flush()
    return contact.id


def _add_source(session, smid):
    source = ProjectSource(project_id=smid, doi="DOI1", pmid=12345678)
    session.add(source)
    session.flush()


def _add_project(session):
    smid = utils.gen_short_uuid(ProjectService.SMID_LENGTH, [])
    project = Project(
        id=smid,
        title="Project Title",
        summary="Project summary",
        contact_id=_add_contact(session),
        date_published=datetime.fromisoformat("2024-01-01"),
        date_added=datetime(2024, 6, 17, 12, 0, 0),
    )
    session.add(project)
    session.flush()
    _add_source(session, smid)
    session.commit()
    return smid


@pytest.fixture
def project(Session, freezer):
    freezer.move_to("2024-06-17 12:00:00")
    session = Session()
    _add_setup(session)
    _add_selection(session)
    return _add_project(session)


EXON = """
1\t65418\t65433\tG\t.\t+\tENSG00000000001\tprotein_coding
1\t65418\t65500\tF\t.\t-\tENSG00000000002\tunprocessed_pseudogene
1\t65519\t65573\tG\t.\t+\tENSG00000000001\tprotein_coding
1\t69036\t71585\tG\t.\t+\tENSG00000000001\tprotein_coding
"""

CDS = """1\t65564\t65573\tG\t.\t+\tENSG00000000001\tprotein_coding
1\t69036\t70005\tG \t.\t+\tENSG00000000001\tprotein_coding
"""

UTR5 = """1\t65418\t65433\tG\t.\t+\tENSG00000000001\tprotein_coding
1\t65519\t65564\tG\t.\t+\tENSG00000000001\tprotein_coding
"""

UTR3 = """1\t70008\t71585\tG\t.\t+\tENSG00000000001\tprotein_coding
"""

INTRON = """1\t65433\t65519\tG\t.\t+\tENSG00000000001\tprotein_coding
1\t65573\t69036\tG\t.\t+\tENSG00000000001\tprotein_coding
"""

INTERGENIC = """1\t0\t11868"""

FEATURES = {
    "exon.bed": EXON,
    "five_prime_utr.bed": UTR5,
    "three_prime_utr.bed": UTR3,
    "CDS.bed": CDS,
    "intron.bed": INTRON,
    "intergenic.bed": INTERGENIC,
}


def _write_chrom_file(data_path):
    d = data_path.ASSEMBLY_PATH / "Homo_sapiens" / "GRCh38"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "chrom.sizes", "w") as fh:
        fh.write("1\t248956422\n")


def _add_genomic_annotation(session):
    annotation = GenomicAnnotation(
        id="ENSG00000000001", annotation_id=1, name="G", biotype="protein_coding"
    )
    session.add(annotation)
    session.commit()


@pytest.fixture
def annotation(Session, data_path):
    _write_chrom_file(data_path)
    _add_genomic_annotation(Session())
    d = data_path.ANNOTATION_PATH / "Homo_sapiens" / "GRCh38" / "110"
    d.mkdir(parents=True, exist_ok=True)
    for feature, string in FEATURES.items():
        with open(d / feature, "w") as fh:
            fh.write(string)


def get_bedtools_service(tmp_path):
    return BedToolsService(tmp_path=tmp_path)


def get_assembly_service(session, external_service):
    return AssemblyService(session=session, external_service=external_service)


def get_annotation_service(
    session, assembly_service, data_service, bedtools_service, external_service
):
    return AnnotationService(
        session=session,
        services_by_annotation_source={
            AnnotationSource.ENSEMBL: EnsemblAnnotationService(
                session=session,
                assembly_service=assembly_service,
                data_service=data_service,
                bedtools_service=bedtools_service,
                external_service=external_service,
            ),
            AnnotationSource.GTRNADB: GtRNAdbAnnotationService(
                session=session,
                assembly_service=assembly_service,
                data_service=data_service,
                bedtools_service=bedtools_service,
                external_service=external_service,
            ),
        },
    )


def get_file_service(session, tmp_path):
    return FileService(session=session, temp_path=tmp_path, upload_path=tmp_path)


def get_data_service(session):
    return DataService(session=session)


def get_external_service(file_service):
    return ExternalService(file_service=file_service)


def get_dataset_service(session, tmp_path):
    bedtools_service = get_bedtools_service(tmp_path)
    file_service = get_file_service(session, tmp_path)
    data_service = get_data_service(session)
    external_service = get_external_service(file_service)
    assembly_service = get_assembly_service(session, external_service)
    annotation_service = get_annotation_service(
        session, assembly_service, data_service, bedtools_service, external_service
    )
    return DatasetService(
        session=session,
        bedtools_service=bedtools_service,
        annotation_service=annotation_service,
        assembly_service=assembly_service,
    )


EUF_FILE = """
#fileformat=bedRModv1.7
#organism=9606
#modification_type=RNA
#assembly=GRCh38
#annotation_source=Annotation
#annotation_version=Version
#sequencing_platform=Sequencing platform
#basecalling=
#bioinformatics_workflow=Workflow
#experiment=Description of experiment.
#external_source=
#chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\titermRgb\tcoverage\tfrequency
1\t65420\t65421\tm6A\t1\t+\t65420\t65421\t0,0,0\t1\t1
1\t65565\t65566\tm6A\t2\t+\t65565\t65566\t0,0,0\t2\t2
1\t71500\t71501\tm6A\t3\t+\t71500\t71501\t0,0,0\t3\t3
1\t65580\t65581\tm6A\t4\t+\t65580\t65581\t0,0,0\t4\t4
1\t0\t1\tm6A\t5\t+\t0\t1\t0,0,0\t5\t5
"""


def test_import_simple(Session, project, annotation, tmp_path):
    service = get_dataset_service(Session(), tmp_path)
    file = StringIO(EUF_FILE)
    eufid = service.import_dataset(
        file,
        source="test",
        smid=project,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
    )

    with Session() as session:
        dataset = session.get_one(Dataset, eufid)
        assert dataset.title == "title"
        assert dataset.project_id == project
        assert dataset.technology_id == 1
        assert dataset.organism_id == 1
        assert dataset.date_added == datetime(2024, 6, 17, 12, 0, 0)
        assert dataset.modification_type == "RNA"
        assert dataset.sequencing_platform == "Sequencing platform"
        assert dataset.basecalling is None
        assert dataset.bioinformatics_workflow == "Workflow"
        assert dataset.experiment == "Description of experiment."
        assert dataset.external_source is None

        # add checks for records and annotated records

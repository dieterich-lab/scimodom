import json
from pathlib import Path
import re

import pytest
from flask import Flask
from sqlalchemy import func, select

from scimodom.database.models import (
    Project,
    Selection,
    UserProjectAssociation,
    User,
    DataAnnotation,
    Data,
    DatasetModificationAssociation,
    BamFile,
    Dataset,
    ProjectSource,
    ProjectContact,
)
from scimodom.cli.project import project_cli
from scimodom.services.annotation import AnnotationService
from scimodom.services.annotation.ensembl import EnsemblAnnotationService
from scimodom.services.assembly import AssemblyService
from scimodom.services.bedtools import BedToolsService
from scimodom.services.data import DataService
from scimodom.services.dataset import DatasetService
from scimodom.services.external import ExternalService
from scimodom.services.gene import GeneService
from scimodom.services.file import FileService
from scimodom.services.mail import MailService
from scimodom.services.permission import PermissionService
from scimodom.services.project import ProjectService
from scimodom.services.selection import SelectionService
from scimodom.services.url import UrlService
from scimodom.services.user import UserService
from scimodom.services.validator import ValidatorService
from scimodom.services.web import WebService
from scimodom.utils.specs.enums import AnnotationSource, UserState

DATA_DIR = Path(Path(__file__).parent, "data")


JSON_TEMPLATE = """
{
    "title": "Test title",
    "summary": "Long summary.",
    "contact_name": "Surname, Forename",
    "contact_institution": "Institution",
    "contact_email": "test@email.de",
    "date_published": null,
    "external_sources": [],
    "metadata": [
        {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "Tech-seq",
            "method_id": "01d26feb",
            "organism": {
                "taxa_id": 9606,
                "cto": "HeLa",
                "assembly_name": "GRCh38",
                "assembly_id": null
            },
            "note": "file=filename1.bedrmod, title=Title dataset 1"
        },
        {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "Tech-seq",
            "method_id": "01d26feb",
            "organism": {
                "taxa_id": 10090,
                "cto": "mESC",
                "assembly_name": "GRCm38",
                "assembly_id": null
            },
            "note": "file=filename2.bedrmod, title=Title dataset 2"
        }
    ]
}
"""


def _get_permission_service(Session):
    return PermissionService(Session())


def _get_file_service(Session, tmp_path):
    return FileService(
        session=Session(),
        data_path=Path(tmp_path, "t_data"),
        temp_path=Path(tmp_path, "t_temp"),
        upload_path=Path(tmp_path, "t_upload"),
        import_path=Path(tmp_path, "t_import"),
    )


def _get_user_service(Session):
    return UserService(
        session=Session(),
        mail_service=MailService(
            url_service=UrlService(http_public_url="HTTP_PUBLIC_URL"),
            smtp_server="SMTP_SERVER",
            from_address="SMTP_FROM_ADDRESS",
            notification_address="NOTIFICATION_ADDRESS",
        ),
    )


def _get_assembly_service(Session, tmp_path):
    return AssemblyService(
        session=Session(),
        external_service=ExternalService(
            file_service=_get_file_service(Session, tmp_path)
        ),
        web_service=WebService(),
        file_service=_get_file_service(Session, tmp_path),
    )


def _get_bedtools_service(Session, tmp_path):
    return BedToolsService(tmp_path=Path(tmp_path, "t_temp"))


def _get_gene_service(Session, tmp_path):
    return GeneService(
        session=Session(), file_service=_get_file_service(Session, tmp_path)
    )


def _get_annotation_service(Session, tmp_path):
    return AnnotationService(
        session=Session(),
        services_by_annotation_source={
            AnnotationSource.ENSEMBL: EnsemblAnnotationService(
                session=Session(),
                data_service=DataService(Session()),
                bedtools_service=_get_bedtools_service(Session, tmp_path),
                external_service=ExternalService(
                    file_service=_get_file_service(Session, tmp_path)
                ),
                web_service=WebService(),
                gene_service=_get_gene_service(Session, tmp_path),
                file_service=_get_file_service(Session, tmp_path),
            ),
        },
    )


def _get_validator_service(Session, tmp_path):
    return ValidatorService(
        session=Session(),
        annotation_service=_get_annotation_service(Session, tmp_path),
        assembly_service=_get_assembly_service(Session, tmp_path),
        bedtools_service=_get_bedtools_service(Session, tmp_path),
    )


def _get_dataset_service(Session, tmp_path):
    return DatasetService(
        session=Session(),
        annotation_service=_get_annotation_service(Session, tmp_path),
        file_service=_get_file_service(Session, tmp_path),
        validator_service=_get_validator_service(Session, tmp_path),
    )


def _get_selection_service(Session, tmp_path):
    return SelectionService(
        session=Session(), gene_service=_get_gene_service(Session, tmp_path)
    )


def _get_project_service(Session, tmp_path):
    return ProjectService(
        session=Session(),
        file_service=_get_file_service(Session, tmp_path),
        selection_service=_get_selection_service(Session, tmp_path),
    )


@pytest.fixture
def test_runner():
    app = Flask(__name__)
    app.register_blueprint(project_cli)
    yield app.test_cli_runner()


@pytest.fixture
def mock_services(mocker, Session, tmp_path):
    mocker.patch(
        "scimodom.cli.project.get_assembly_service",
        return_value=_get_assembly_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.project.get_dataset_service",
        return_value=_get_dataset_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.project.get_file_service",
        return_value=_get_file_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.project.get_permission_service",
        return_value=_get_permission_service(Session),
    )
    mocker.patch(
        "scimodom.cli.project.get_project_service",
        return_value=_get_project_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.project.get_selection_service",
        return_value=_get_selection_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.project.get_user_service",
        return_value=_get_user_service(Session),
    )


# tests


@pytest.mark.datafiles(Path(DATA_DIR, "metadata.csv"))
def test_create_template(test_runner, datafiles, capsys, setup, mock_services):
    args = [
        "project",
        "create-template",
        "--title",
        "Test title",
        "--summary",
        "Long summary.",
        "--surname",
        "Surname",
        "--forename",
        "Forename",
        "--institution",
        "Institution",
        "--email",
        "test@email.de",
        Path(datafiles, "metadata.csv").as_posix(),
    ]

    result = test_runner.invoke(args=args, input="y")
    # exceptions are handled gracefully so exit code will likely always be 0...
    assert result.exit_code == 0
    # result.stdout or output does not capture secho consistently...
    uuid = re.search("ID: '(.*)'.", capsys.readouterr().out).group(1)
    expected_template = json.loads(JSON_TEMPLATE)
    project_template = json.load(
        open(Path(datafiles, "t_data", "metadata", "project_requests", f"{uuid}.json"))
    )
    assert project_template == expected_template


@pytest.mark.datafiles(Path(DATA_DIR, "metadata.csv"))
def test_create_template_use_ids(test_runner, datafiles, capsys, setup, mock_services):
    dataset_csv = Path(datafiles, "metadata.csv")
    text = dataset_csv.read_text()
    text = text.replace("m6A", "2000000006A")
    text = text.replace("Enzyme/protein-assisted sequencing", "01d26feb")
    dataset_csv.write_text(text)

    args = [
        "project",
        "create-template",
        "--title",
        "Test title",
        "--summary",
        "Long summary.",
        "--surname",
        "Surname",
        "--forename",
        "Forename",
        "--institution",
        "Institution",
        "--email",
        "test@email.de",
        dataset_csv.as_posix(),
        "--use-mod-ids",
        "--use-method-ids",
    ]

    result = test_runner.invoke(args=args, input="y")
    # exceptions are handled gracefully so exit code will likely always be 0...
    assert result.exit_code == 0
    # result.stdout or output does not capture secho consistently...
    uuid = re.search("ID: '(.*)'.", capsys.readouterr().out).group(1)
    expected_template = json.loads(JSON_TEMPLATE)
    project_template = json.load(
        open(Path(datafiles, "t_data", "metadata", "project_requests", f"{uuid}.json"))
    )
    assert project_template == expected_template


@pytest.mark.datafiles(Path(DATA_DIR, "metadata.csv"))
def test_create_template_extra_columns(
    test_runner, datafiles, capsys, setup, mock_services
):
    dataset_csv = Path(datafiles, "metadata.csv")
    text = dataset_csv.read_text()
    text = text.replace("extra1", "assembly_id")
    text = text.replace("extra2", "note")
    dataset_csv.write_text(text)

    modified_template = JSON_TEMPLATE.replace(
        "file=filename1.bedrmod, title=Title dataset 1", "note1"
    )
    modified_template = modified_template.replace(
        "file=filename2.bedrmod, title=Title dataset 2", "note2"
    )
    modified_template = modified_template.replace(
        '"assembly_id": null', '"assembly_id": 1', 1
    )
    modified_template = modified_template.replace(
        '"assembly_id": null', '"assembly_id": 2'
    )

    args = [
        "project",
        "create-template",
        "--title",
        "Test title",
        "--summary",
        "Long summary.",
        "--surname",
        "Surname",
        "--forename",
        "Forename",
        "--institution",
        "Institution",
        "--email",
        "test@email.de",
        dataset_csv.as_posix(),
    ]

    result = test_runner.invoke(args=args, input="y")
    # exceptions are handled gracefully so exit code will likely always be 0...
    assert result.exit_code == 0
    # result.stdout or output does not capture secho consistently...
    uuid = re.search("ID: '(.*)'.", capsys.readouterr().out).group(1)
    expected_template = json.loads(modified_template)
    project_template = json.load(
        open(Path(datafiles, "t_data", "metadata", "project_requests", f"{uuid}.json"))
    )
    assert project_template == expected_template


def test_add_project(Session, test_runner, tmp_path, capsys, setup, mock_services):
    d = tmp_path / "t_data" / "metadata" / "project_requests"
    request_template = d / "XXXXXXXXXXXX.json"
    with open(request_template, "w") as fh:
        json.dump(json.loads(JSON_TEMPLATE), fh, indent=4)

    with Session() as session:
        session.add(User(email="test@email.de", state=UserState.active))
        session.commit()

    result = test_runner.invoke(
        args=["project", "add", "XXXXXXXXXXXX", "--add-user"], input="y"
    )
    # exceptions are handled gracefully so exit code will likely always be 0...
    assert result.exit_code == 0
    # result.stdout or output does not capture secho consistently...
    smid = re.search("SMID: '(.*)'.", capsys.readouterr().out).group(1)
    d = tmp_path / "t_data" / "metadata"
    project_template = d / f"{smid}.json"

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Selection)) == 2
        assert session.scalar(select(func.count()).select_from(Project)) == 1
        assert (
            session.scalar(select(func.count()).select_from(UserProjectAssociation))
            == 1
        )
    assert Path(request_template).exists() is False
    assert Path(project_template).exists() is True


def test_delete_project(
    Session, test_runner, tmp_path, bam_file, annotation, mock_services
):
    d = tmp_path / "t_data" / "metadata"
    project_template = Path(d, "12345678.json")
    project_template.touch()

    d = tmp_path / "t_data" / "cache" / "gene" / "selection"
    gene_cache = []
    for r in range(1, 5):
        p = Path(d, str(r))
        p.touch()
        gene_cache.append(p)

    d = tmp_path / "t_data" / "bam_files"
    bam_files = []
    with Session() as session:
        bam_storage = session.execute(select(BamFile.storage_file_name)).scalars().all()
        for r in bam_storage:
            p = Path(d, str(r))
            p.touch()
            bam_files.append(p)

    result = test_runner.invoke(args=["project", "delete", "12345678"], input="y")
    # exceptions are handled gracefully so exit code will likely always be 0...
    assert result.exit_code == 0

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Selection)) == 0
        assert session.scalar(select(func.count()).select_from(DataAnnotation)) == 0
        assert session.scalar(select(func.count()).select_from(Data)) == 0
        assert (
            session.scalar(
                select(func.count()).select_from(DatasetModificationAssociation)
            )
            == 1
        )
        assert session.scalar(select(func.count()).select_from(BamFile)) == 0
        assert session.scalar(select(func.count()).select_from(Dataset)) == 1
        assert session.scalar(select(func.count()).select_from(ProjectSource)) == 0
        assert (
            session.scalar(select(func.count()).select_from(UserProjectAssociation))
            == 0
        )
        assert session.scalar(select(func.count()).select_from(Project)) == 1
        assert session.scalar(select(func.count()).select_from(ProjectContact)) == 1

    assert project_template.exists() is False
    for p in gene_cache:
        assert p.exists() is False
    for p in bam_files:
        assert p.exists() is False

import datetime
import json
from io import StringIO

import pytest
from sqlalchemy.exc import NoResultFound

from scimodom.services.administration.ingestion import (
    ProjectIngestionService,
    ProjectRequestInfo,
    ProjectTemplateError,
    UserAssociationError,
)
from scimodom.services.assembly import AssemblyNotFoundError
from scimodom.services.user import NoSuchUser
from scimodom.utils.dtos.project import ProjectTemplate

CSV = """file,title,rna_type,modification,taxa_id,cto,assembly,technology,method
f1.bedrmod,Title 1,WTS,m6A,9606,HeLa,GRCh38,Tech-seq,Method 1
f2.bedrmod,Title 2,WTS,m6A,10090,mESC, GRCm38 ,Tech-seq,Method 1
"""

INFO = ProjectRequestInfo(
    title="Title",
    summary="Summary",
    surname="Surname",
    forename="Forename",
    institution="Institution",
    email="test@email.de",
)

TEMPLATE = {
    "title": "Title",
    "summary": "Summary",
    "contact_name": "Surname, Forename",
    "contact_institution": "Institution",
    "contact_email": "test@email.de",
    "date_published": None,
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
                "assembly_id": None,
            },
            "note": "file=f1.bedrmod, title=Title 1",
        }
    ],
}


@pytest.fixture
def mocks(mocker):
    class Mocks:
        project = mocker.Mock()
        assembly = mocker.Mock()
        utilities = mocker.Mock()
        file = mocker.Mock()
        permission = mocker.Mock()
        user = mocker.Mock()

    Mocks.utilities.get_modomics_id_by_short_name.return_value = "2000000006A"
    Mocks.utilities.get_method_id_by_name.return_value = "01d26feb"
    return Mocks


@pytest.fixture
def service(mocks):
    return ProjectIngestionService(
        project_service=mocks.project,
        assembly_service=mocks.assembly,
        utilities_service=mocks.utilities,
        file_service=mocks.file,
        permission_service=mocks.permission,
        user_service=mocks.user,
    )


def _csv(tmp_path, content=CSV):
    path = tmp_path / "datasets.csv"
    path.write_text(content)
    return path


def _request_file(mocks, template):
    mocks.file.open_project_request_file.return_value = StringIO(json.dumps(template))


# build_template


def test_build_template(service, mocks, tmp_path):
    template = service.build_template(_csv(tmp_path), INFO)
    assert template.contact_name == "Surname, Forename"
    assert len(template.metadata) == 2
    assert template.metadata[1].organism.assembly_name == "GRCm38"  # stripped
    assert template.metadata[0].modomics_id == "2000000006A"
    assert template.metadata[0].note == "file=f1.bedrmod, title=Title 1"
    mocks.utilities.get_modomics_id_by_short_name.assert_any_call("m6A")
    # no side effects
    mocks.project.create_project_request.assert_not_called()


def test_build_template_use_ids(service, mocks, tmp_path):
    template = service.build_template(
        _csv(tmp_path), INFO, use_mod_ids=True, use_method_ids=True
    )
    assert template.metadata[0].modomics_id == "m6A"
    assert template.metadata[0].method_id == "Method 1"
    mocks.utilities.get_modomics_id_by_short_name.assert_not_called()
    mocks.utilities.get_method_id_by_name.assert_not_called()


def test_build_template_sources_and_date(service, tmp_path):
    info = ProjectRequestInfo(
        title="T",
        summary="S",
        surname="A",
        forename="B",
        institution="I",
        email="test@email.de",
        published=datetime.date(2024, 1, 2),
        doi=("10.1/abc", "null"),
        pmid=(0, 123),
    )
    template = service.build_template(_csv(tmp_path), info)
    assert [(s.doi, s.pmid) for s in template.external_sources] == [
        ("10.1/abc", None),
        (None, 123),
    ]
    assert template.date_published.date() == datetime.date(2024, 1, 2)


def test_build_template_missing_header(service, tmp_path):
    path = _csv(tmp_path, CSV.replace("technology", "tech"))
    with pytest.raises(ProjectTemplateError, match="Missing header 'technology'"):
        service.build_template(path, INFO)


def test_build_template_unexpected_value(service, mocks, tmp_path):
    mocks.utilities.get_modomics_id_by_short_name.side_effect = NoResultFound("x")
    with pytest.raises(ProjectTemplateError, match="unexpected values"):
        service.build_template(_csv(tmp_path), INFO)


def test_build_template_invalid_value(service, tmp_path):
    path = _csv(tmp_path, CSV.replace("9606", "-1"))
    with pytest.raises(ProjectTemplateError, match="unexpected values"):
        service.build_template(path, INFO)


def test_build_template_no_such_file(service, tmp_path):
    with pytest.raises(ProjectTemplateError, match="Cannot read"):
        service.build_template(tmp_path / "missing.csv", INFO)


def test_save_request(service, mocks):
    mocks.project.create_project_request.return_value = "UUID"
    assert service.save_request("template") == "UUID"
    mocks.project.create_project_request.assert_called_once_with("template")


# load_template


def test_load_template(service, mocks):
    _request_file(mocks, TEMPLATE)
    mocks.assembly.get_by_taxa_and_name.return_value.id = 7
    template = service.load_template("UUID")
    assert template.metadata[0].organism.assembly_id == 7
    mocks.assembly.get_by_taxa_and_name.assert_called_once_with(9606, "GRCh38")


def test_load_template_invalid(service, mocks):
    _request_file(mocks, {"title": "x"})
    with pytest.raises(ProjectTemplateError, match="Failed to read template"):
        service.load_template("UUID")


def test_load_template_no_such_request(service, mocks):
    mocks.file.open_project_request_file.side_effect = FileNotFoundError("x")
    with pytest.raises(ProjectTemplateError, match="Failed to read template"):
        service.load_template("UUID")


def test_assign_assembly_ids_given_id_is_checked(service, mocks):
    template = ProjectTemplate.model_validate(TEMPLATE)
    template.metadata[0].organism.assembly_id = 3
    service.assign_assembly_ids(template)
    mocks.assembly.get_by_id.assert_called_once_with(3)
    mocks.assembly.get_by_taxa_and_name.assert_not_called()
    assert template.metadata[0].organism.assembly_id == 3


@pytest.mark.parametrize("assembly_id", [None, 3])
def test_assign_assembly_ids_not_found(service, mocks, assembly_id):
    template = ProjectTemplate.model_validate(TEMPLATE)
    template.metadata[0].organism.assembly_id = assembly_id
    mocks.assembly.get_by_id.side_effect = NoResultFound
    mocks.assembly.get_by_taxa_and_name.side_effect = NoResultFound
    with pytest.raises(AssemblyNotFoundError) as exc:
        service.assign_assembly_ids(template)
    assert str(exc.value) == "No such assembly 'GRCh38' for organism '9606'"


# create_project


def _template():
    return ProjectTemplate.model_validate(TEMPLATE)


def test_create_project(service, mocks):
    mocks.project.create_project.return_value = "SMID1"
    template = _template()
    result = service.create_project(template, "UUID")
    assert (result.project_id, result.user_added) == ("SMID1", None)
    mocks.project.create_project.assert_called_once_with(template, "UUID")
    mocks.user.get_user_by_email.assert_not_called()


def test_create_project_fails(service, mocks):
    mocks.project.create_project.side_effect = RuntimeError()
    with pytest.raises(RuntimeError):
        service.create_project(_template(), "UUID", add_user=True)
    mocks.user.get_user_by_email.assert_not_called()


def test_create_project_add_user(service, mocks):
    mocks.project.create_project.return_value = "SMID1"
    result = service.create_project(_template(), "UUID", add_user=True)
    assert result.user_added is True
    mocks.user.get_user_by_email.assert_called_once_with("test@email.de")
    mocks.permission.insert_into_user_project_association.assert_called_once_with(
        mocks.user.get_user_by_email.return_value, "SMID1"
    )


def test_create_project_no_such_user(service, mocks):
    mocks.project.create_project.return_value = "SMID1"
    mocks.user.get_user_by_email.side_effect = NoSuchUser("x")
    result = service.create_project(_template(), "UUID", add_user=True)
    assert (result.project_id, result.user_added) == ("SMID1", False)


def test_create_project_user_association_fails(service, mocks):
    mocks.project.create_project.return_value = "SMID1"
    mocks.permission.insert_into_user_project_association.side_effect = RuntimeError()
    with pytest.raises(UserAssociationError) as exc:
        service.create_project(_template(), "UUID", add_user=True)
    assert exc.value.project_id == "SMID1"
    assert "Project 'SMID1' was created" in str(exc.value)


# add_user_to_project


def test_add_user_to_project(service, mocks):
    service.add_user_to_project("test@email.de", "SMID1")
    mocks.project.get_by_id.assert_called_once_with("SMID1")
    mocks.permission.insert_into_user_project_association.assert_called_once_with(
        mocks.user.get_user_by_email.return_value, "SMID1"
    )


def test_add_user_to_project_no_such_project(service, mocks):
    mocks.project.get_by_id.side_effect = NoResultFound
    with pytest.raises(NoResultFound):
        service.add_user_to_project("test@email.de", "SMID1")
    mocks.permission.insert_into_user_project_association.assert_not_called()

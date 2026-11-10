import datetime
import json
from io import StringIO

import pytest
from sqlalchemy.exc import NoResultFound

from scimodom.services.administration.ingestion import (
    ProjectIngestionService,
    _parse_dataset_note,
    ProjectRequestInfo,
    ProjectTemplateError,
    UserAssociationError,
)
from scimodom.services.assembly import AssemblyNotFoundError, AssemblyService
from scimodom.services.dataset import DatasetService
from scimodom.services.file import FileService
from scimodom.services.permission import PermissionService
from scimodom.services.project import ProjectService
from scimodom.services.user import UserService
from scimodom.services.utilities import UtilitiesService
from scimodom.services.user import NoSuchUser
from scimodom.utils.dtos.project import ProjectTemplate
from scimodom.utils.specs.enums import AnnotationSource

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
        project = mocker.create_autospec(ProjectService, instance=True)
        assembly = mocker.create_autospec(AssemblyService, instance=True)
        utilities = mocker.create_autospec(UtilitiesService, instance=True)
        file = mocker.create_autospec(FileService, instance=True)
        permission = mocker.create_autospec(PermissionService, instance=True)
        user = mocker.create_autospec(UserService, instance=True)
        dataset = mocker.create_autospec(DatasetService, instance=True)

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
        dataset_service=mocks.dataset,
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
    with pytest.raises(ProjectTemplateError, match="DATASET_CSV values not found"):
        service.build_template(_csv(tmp_path), INFO)


def test_build_template_invalid_value(service, tmp_path):
    path = _csv(tmp_path, CSV.replace("9606", "-1"))
    with pytest.raises(
        ProjectTemplateError, match="Unexpected DATASET_CSV values or arguments"
    ):
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


# batch import


BATCH_TEMPLATE = {
    "title": "Batch",
    "summary": "Summary",
    "contact_name": "Surname, Forename",
    "contact_institution": "Institution",
    "contact_email": "test@email.de",
    "date_published": None,
    "external_sources": [],
    "metadata": [],
}


def _entry(filename, title="T", rna="WTS", modomics="2000000006A", **organism):
    organism = {
        "taxa_id": 9606,
        "cto": "HeLa",
        "assembly_name": "GRCh38",
        "assembly_id": 1,
        **organism,
    }
    return {
        "rna": rna,
        "modomics_id": modomics,
        "tech": "Tech-seq",
        "method_id": "01d26feb",
        "organism": organism,
        "note": f"file={filename}, title={title}",
    }


def _batch_request(mocks, *entries):
    _request_file(mocks, {**BATCH_TEMPLATE, "metadata": list(entries)})


def _files(tmp_path, *names):
    for name in names:
        (tmp_path / name).write_text("data")


@pytest.mark.parametrize(
    "note, expected",
    [
        ("file=a.bedrmod, title=My title", ("a.bedrmod", "My title")),
        ("file=a.bedrmod,title=  x, y ", ("a.bedrmod", "x, y")),
    ],
)
def test_parse_dataset_note(note, expected):
    assert _parse_dataset_note(note) == expected


@pytest.mark.parametrize("note", [None, "nothing", "file=a.bedrmod"])
def test_parse_dataset_note_fail(note):
    with pytest.raises(ProjectTemplateError):
        _parse_dataset_note(note)


def test_plan_batch_import(service, mocks, tmp_path):
    _files(tmp_path, "a.bedrmod", "b.bedrmod")
    # a.bedrmod has 2 modifications
    _batch_request(
        mocks,
        _entry("a.bedrmod", "Title A", modomics="2000000006A"),
        _entry("b.bedrmod", "Title B", rna="tRNA"),
        _entry("a.bedrmod", "Title A", modomics="2000000007A"),
    )
    plan = service.plan_batch_import(tmp_path, "UUID")
    assert plan.request_uuid == "UUID"
    assert [d.filename for d in plan.datasets] == ["a.bedrmod", "b.bedrmod"]
    a, b = plan.datasets
    assert a.title == "Title A"
    assert a.modifications == (("WTS", "2000000006A"), ("WTS", "2000000007A"))
    assert b.modifications == (("tRNA", "2000000006A"),)
    # annotation source from the RNA type of each dataset
    assert a.annotation_source is AnnotationSource.ENSEMBL
    assert b.annotation_source is AnnotationSource.GTRNADB
    assert (a.assembly_id, a.taxa_id, a.cto) == (1, 9606, "HeLa")
    assert (a.method_id, a.tech) == ("01d26feb", "Tech-seq")
    assert a.file_path == tmp_path / "a.bedrmod"
    # nothing is written
    mocks.project.create_project.assert_not_called()
    mocks.dataset.import_dataset.assert_not_called()


def test_plan_batch_import_mixed_rna_types_in_a_file(service, mocks, tmp_path):
    _files(tmp_path, "a.bedrmod")
    _batch_request(
        mocks,
        _entry("a.bedrmod", "Title A"),
        _entry("a.bedrmod", "Title A", rna="tRNA", modomics="2000000007A"),
    )
    with pytest.raises(ProjectTemplateError, match="different RNA types: WTS, tRNA"):
        service.plan_batch_import(tmp_path, "UUID")


def test_plan_batch_import_rna_type_not_implemented(service, mocks, tmp_path):
    _files(tmp_path, "a.bedrmod", "b.bedrmod")
    _batch_request(
        mocks,
        _entry("a.bedrmod", rna="rRNA"),
        _entry("b.bedrmod", rna="WTS"),
    )
    with pytest.raises(ProjectTemplateError) as exc_info:
        service.plan_batch_import(tmp_path, "UUID")
    assert "'a.bedrmod': RNA type 'rRNA' is not implemented" in str(exc_info.value)
    assert "b.bedrmod" not in str(exc_info.value)


def test_plan_batch_import_reports_all_problems(service, mocks, tmp_path):
    _files(tmp_path, "a.bedrmod")
    bad_note = _entry("x")
    bad_note["note"] = "nothing"
    _batch_request(
        mocks,
        _entry("a.bedrmod", "Title A"),
        _entry("a.bedrmod", "Other title"),  # same file, different title
        _entry("a.bedrmod", cto="Other"),  # same file, different organism
        _entry("missing.bedrmod"),
        _entry("../outside.bedrmod"),
        bad_note,
    )
    with pytest.raises(ProjectTemplateError) as exc:
        service.plan_batch_import(tmp_path, "UUID")
    message = str(exc.value)
    assert message.startswith("Invalid batch import:")
    assert "Metadata entry 2: file 'a.bedrmod' is repeated" in message
    assert "Metadata entry 3: file 'a.bedrmod' is repeated" in message
    assert "File 'missing.bedrmod' not found" in message
    assert "File '../outside.bedrmod' is not under the input directory" in message
    assert "Metadata entry 6: Unable to match" in message


def test_plan_batch_import_absolute_file_name(service, mocks, tmp_path):
    outside = tmp_path / "outside.bedrmod"
    outside.write_text("data")
    inner = tmp_path / "inner"
    inner.mkdir()
    _batch_request(mocks, _entry(outside.as_posix()))
    with pytest.raises(ProjectTemplateError, match="not under the input directory"):
        service.plan_batch_import(inner, "UUID")


def test_plan_batch_import_invalid_request(service, mocks, tmp_path):
    mocks.file.open_project_request_file.side_effect = FileNotFoundError("x")
    with pytest.raises(ProjectTemplateError, match="Failed to read template"):
        service.plan_batch_import(tmp_path, "UUID")


def test_plan_batch_import_assembly_not_found(service, mocks, tmp_path):
    _batch_request(mocks, _entry("a.bedrmod", assembly_id=None))
    mocks.assembly.get_by_taxa_and_name.side_effect = NoResultFound
    with pytest.raises(AssemblyNotFoundError):
        service.plan_batch_import(tmp_path, "UUID")


def _plan(service, mocks, tmp_path, *entries):
    _files(tmp_path, "a.bedrmod", "b.bedrmod")
    _batch_request(mocks, *entries)
    return service.plan_batch_import(tmp_path, "UUID")


def test_import_batch_datasets(service, mocks, tmp_path):
    plan = _plan(
        service,
        mocks,
        tmp_path,
        _entry("a.bedrmod", "Title A"),
        _entry("a.bedrmod", "Title A", modomics="2000000007A"),
    )
    mocks.utilities.get_modification_id.side_effect = [10, 11]
    mocks.utilities.get_organism_id.return_value = 20
    mocks.utilities.get_technology_id.return_value = 30
    mocks.dataset.import_dataset.return_value = "EUFID1"

    outcomes = list(service.import_batch_datasets(plan, "SMID1"))

    assert [(o.dataset.filename, o.dataset_id, o.is_imported) for o in outcomes] == [
        ("a.bedrmod", "EUFID1", True)
    ]
    mocks.utilities.get_modification_id.assert_any_call("WTS", "2000000006A")
    mocks.utilities.get_modification_id.assert_any_call("WTS", "2000000007A")
    mocks.utilities.get_organism_id.assert_called_once_with(9606, "HeLa")
    mocks.utilities.get_technology_id.assert_called_once_with("01d26feb", "Tech-seq")
    call = mocks.dataset.import_dataset.call_args
    assert call.kwargs == {
        "source": (tmp_path / "a.bedrmod").as_posix(),
        "project_id": "SMID1",
        "title": "Title A",
        "assembly_id": 1,
        "modification_ids": [10, 11],
        "organism_id": 20,
        "technology_id": 30,
        "annotation_source": AnnotationSource.ENSEMBL,
    }


def test_import_batch_datasets_failure_does_not_stop_others(service, mocks, tmp_path):
    plan = _plan(
        service, mocks, tmp_path, _entry("a.bedrmod", "A"), _entry("b.bedrmod", "B")
    )
    failure = RuntimeError("invalid file")
    mocks.dataset.import_dataset.side_effect = [failure, "EUFID2"]
    outcomes = list(service.import_batch_datasets(plan, "SMID1"))
    assert [o.is_imported for o in outcomes] == [False, True]
    assert outcomes[0].error is failure
    assert outcomes[0].dataset_id is None
    assert outcomes[1].dataset_id == "EUFID2"


def test_import_batch_datasets_unresolved_id_is_a_dataset_failure(
    service, mocks, tmp_path
):
    plan = _plan(
        service, mocks, tmp_path, _entry("a.bedrmod", "A"), _entry("b.bedrmod", "B")
    )
    mocks.utilities.get_organism_id.side_effect = [NoResultFound("x"), 20]
    mocks.dataset.import_dataset.return_value = "EUFID2"
    outcomes = list(service.import_batch_datasets(plan, "SMID1"))
    assert isinstance(outcomes[0].error, NoResultFound)
    assert outcomes[1].is_imported
    assert mocks.dataset.import_dataset.call_count == 1


def test_import_batch_datasets_is_lazy(service, mocks, tmp_path):
    plan = _plan(service, mocks, tmp_path, _entry("a.bedrmod", "A"))
    outcomes = service.import_batch_datasets(plan, "SMID1")
    mocks.dataset.import_dataset.assert_not_called()
    next(outcomes)
    mocks.dataset.import_dataset.assert_called_once()

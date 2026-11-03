import pytest
from sqlalchemy.exc import NoResultFound

from scimodom.services.dataset import DatasetService
from scimodom.services.project import ProjectService
from scimodom.services.selection import SelectionService
from scimodom.services.administration.deletion import (
    ProjectDeletionError,
    ProjectDeletionPlan,
    ProjectDeletionService,
)


def _dataset(mocker, dataset_id, title="title"):
    dataset = mocker.Mock(title=title)
    dataset.id = dataset_id
    return dataset


@pytest.fixture
def services(mocker):
    calls = mocker.Mock()  # records the order of calls across services
    project_service = mocker.create_autospec(ProjectService, instance=True)
    dataset_service = mocker.create_autospec(DatasetService, instance=True)
    selection_service = mocker.create_autospec(SelectionService, instance=True)
    calls.attach_mock(selection_service.delete_selections_by_dataset, "selection")
    calls.attach_mock(dataset_service.delete_dataset, "dataset")
    calls.attach_mock(project_service.delete_project, "project")
    return calls, project_service, dataset_service, selection_service


def _service(services):
    _, project_service, dataset_service, selection_service = services
    return ProjectDeletionService(project_service, dataset_service, selection_service)


def _project(mocker, project_service, dataset_ids):
    project = mocker.Mock(title="Project title")
    project.id = "SMID1"
    project.datasets = [_dataset(mocker, i, f"title {i}") for i in dataset_ids]
    project_service.get_by_id.return_value = project
    return project


def test_plan(mocker, services):
    _project(mocker, services[1], ["A", "B"])
    plan = _service(services).plan("SMID1")
    assert plan.project_id == "SMID1"
    assert plan.title == "Project title"
    assert [(d.id, d.title) for d in plan.datasets] == [
        ("A", "title A"),
        ("B", "title B"),
    ]
    # planning has no side effects
    services[0].selection.assert_not_called()
    services[0].dataset.assert_not_called()
    services[0].project.assert_not_called()


def test_plan_no_such_project(services):
    services[1].get_by_id.side_effect = NoResultFound
    with pytest.raises(NoResultFound):
        _service(services).plan("SMID1")


def test_execute(mocker, services):
    project = _project(mocker, services[1], ["A", "B"])
    a, b = project.datasets
    result = _service(services).execute(ProjectDeletionPlan("SMID1", "t"))
    assert result.project_id == "SMID1"
    assert result.deleted_dataset_ids == ["A", "B"]
    # selections must be handled before the dataset, project is last
    assert services[0].mock_calls == [
        mocker.call.selection(a),
        mocker.call.dataset(a),
        mocker.call.selection(b),
        mocker.call.dataset(b),
        mocker.call.project(project),
    ]


def test_execute_project_without_datasets(mocker, services):
    project = _project(mocker, services[1], [])
    result = _service(services).execute(ProjectDeletionPlan("SMID1", "t"))
    assert result.deleted_dataset_ids == []
    services[0].project.assert_called_once_with(project)


def test_execute_dataset_failure_reports_progress(mocker, services):
    project = _project(mocker, services[1], ["A", "B", "C"])
    failure = RuntimeError()
    services[2].delete_dataset.side_effect = [None, failure]
    with pytest.raises(ProjectDeletionError) as exc:
        _service(services).execute(ProjectDeletionPlan("SMID1", "t"))
    assert exc.value.deleted_dataset_ids == ["A"]
    assert exc.value.remaining_dataset_ids == ["B", "C"]
    assert exc.value.__cause__ is failure
    assert str(exc.value) == (
        "Failure in handling Dataset 'B'. Datasets 'B,C' were not deleted."
    )
    # the project is kept
    services[0].project.assert_not_called()
    assert project.datasets  # untouched


def test_execute_selection_failure(mocker, services):
    _project(mocker, services[1], ["A"])
    services[3].delete_selections_by_dataset.side_effect = RuntimeError()
    with pytest.raises(ProjectDeletionError) as exc:
        _service(services).execute(ProjectDeletionPlan("SMID1", "t"))
    assert exc.value.deleted_dataset_ids == []
    assert exc.value.remaining_dataset_ids == ["A"]
    services[0].dataset.assert_not_called()


def test_execute_project_failure(mocker, services):
    _project(mocker, services[1], ["A"])
    services[1].delete_project.side_effect = RuntimeError()
    with pytest.raises(ProjectDeletionError) as exc:
        _service(services).execute(ProjectDeletionPlan("SMID1", "t"))
    assert exc.value.deleted_dataset_ids == ["A"]
    assert exc.value.remaining_dataset_ids == []
    assert "all its datasets were deleted" in str(exc.value)


def test_execute_can_be_resumed(mocker, services):
    project = _project(mocker, services[1], ["A", "B"])
    services[2].delete_dataset.side_effect = [None, RuntimeError()]
    service = _service(services)
    with pytest.raises(ProjectDeletionError):
        service.execute(ProjectDeletionPlan("SMID1", "t"))
    # the project now only has B, the second run only handles B
    project.datasets = [project.datasets[1]]
    services[2].delete_dataset.side_effect = None
    result = service.execute(ProjectDeletionPlan("SMID1", "t"))
    assert result.deleted_dataset_ids == ["B"]

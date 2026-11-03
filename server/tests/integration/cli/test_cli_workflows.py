import pytest
from flask import Flask

from scimodom.cli.assembly import assembly_cli
from scimodom.cli.project import project_cli
from scimodom.services.administration.assembly.provision import (
    AssemblyProvisioningError,
    AssemblyProvisioningPlan,
    AssemblyProvisioningResult,
)
from scimodom.services.administration.deletion import (
    DatasetSummary,
    ProjectDeletionError,
    ProjectDeletionPlan,
    ProjectDeletionResult,
)
from scimodom.services.administration.ingestion import ProjectIngestionResult
from scimodom.services.assembly import AssemblyNotFoundError
from sqlalchemy.exc import NoResultFound


@pytest.fixture
def test_runner():
    app = Flask(__name__)
    app.register_blueprint(assembly_cli)
    app.register_blueprint(project_cli)
    yield app.test_cli_runner()


# project delete

DELETION_PLAN = ProjectDeletionPlan("SMID1", "Title", [DatasetSummary("A", "t")])


@pytest.fixture
def deletion_service(mocker):
    service = mocker.Mock()
    service.plan.return_value = DELETION_PLAN
    mocker.patch(
        "scimodom.cli.project.get_project_deletion_service", return_value=service
    )
    return service


@pytest.fixture
def sunburst_service(mocker):
    service = mocker.Mock()
    mocker.patch("scimodom.cli.project.get_sunburst_service", return_value=service)
    return service


def test_delete_requires_confirmation_in_non_interactive_mode(
    test_runner, deletion_service
):
    result = test_runner.invoke(args=["project", "delete", "SMID1"])
    assert result.exit_code != 0
    assert "--yes" in result.output
    deletion_service.execute.assert_not_called()


def test_delete(test_runner, deletion_service, sunburst_service):
    deletion_service.execute.return_value = ProjectDeletionResult("SMID1", ["A"])
    result = test_runner.invoke(args=["project", "delete", "--yes", "SMID1"])
    assert result.exit_code == 0
    deletion_service.execute.assert_called_once_with(DELETION_PLAN)
    sunburst_service.trigger_background_update.assert_called_once()


def test_delete_no_such_project(test_runner, deletion_service):
    deletion_service.plan.side_effect = NoResultFound
    result = test_runner.invoke(args=["project", "delete", "--yes", "SMID1"])
    assert result.exit_code != 0
    assert "Project 'SMID1' not found" in result.output
    deletion_service.execute.assert_not_called()


def test_delete_partial_failure_updates_charts_and_fails(
    test_runner, deletion_service, sunburst_service
):
    deletion_service.execute.side_effect = ProjectDeletionError(
        "Failure in handling Dataset 'B'.", ["A"], ["B"]
    )
    result = test_runner.invoke(args=["project", "delete", "--yes", "SMID1"])
    assert result.exit_code != 0
    assert "Run the command again to resume" in result.output
    sunburst_service.trigger_background_update.assert_called_once()


def test_delete_failure_without_progress_does_not_update_charts(
    test_runner, deletion_service, sunburst_service
):
    deletion_service.execute.side_effect = ProjectDeletionError("x", [], ["A"])
    result = test_runner.invoke(args=["project", "delete", "--yes", "SMID1"])
    assert result.exit_code != 0
    sunburst_service.trigger_background_update.assert_not_called()


def test_delete_chart_trigger_failure_is_only_a_warning(
    test_runner, deletion_service, sunburst_service
):
    deletion_service.execute.return_value = ProjectDeletionResult("SMID1", ["A"])
    sunburst_service.trigger_background_update.side_effect = OSError("no flask")
    result = test_runner.invoke(args=["project", "delete", "--yes", "SMID1"])
    assert result.exit_code == 0
    assert "failed to trigger charts update" in result.output


# project add


def test_add_project_no_such_user_is_not_an_error(mocker, test_runner):
    service = mocker.Mock()
    service.load_template.return_value.title = "Title"
    service.load_template.return_value.contact_email = "a@b.de"
    service.create_project.return_value = ProjectIngestionResult("SMID1", False)
    mocker.patch(
        "scimodom.cli.project.get_project_ingestion_service", return_value=service
    )
    result = test_runner.invoke(args=["project", "add", "--yes", "--add-user", "UUID"])
    assert result.exit_code == 0
    assert "SMID: 'SMID1'" in result.output
    assert "No such user 'a@b.de'" in result.output


def test_add_project_assembly_not_found(mocker, test_runner):
    service = mocker.Mock()
    service.load_template.side_effect = AssemblyNotFoundError("No such assembly")
    mocker.patch(
        "scimodom.cli.project.get_project_ingestion_service", return_value=service
    )
    result = test_runner.invoke(args=["project", "add", "--yes", "UUID"])
    assert result.exit_code != 0
    assert "Failed to update template. No such assembly" in result.output
    service.create_project.assert_not_called()


# assembly add

ASSEMBLY_PLAN = AssemblyProvisioningPlan(1, 9606, "GRCh38")


@pytest.fixture
def provisioning_service(mocker):
    service = mocker.Mock()
    service.plan.return_value = ASSEMBLY_PLAN
    mocker.patch(
        "scimodom.cli.assembly.get_assembly_provisioning_service",
        return_value=service,
    )
    return service


def test_assembly_add(test_runner, provisioning_service):
    provisioning_service.execute.return_value = AssemblyProvisioningResult(
        9606, "GRCh38", added=["GRCh37"]
    )
    result = test_runner.invoke(args=["assembly", "add", "--yes", "1"])
    assert result.exit_code == 0
    assert "done with GRCh37" in result.output


def test_assembly_add_other_assemblies_failed_gives_non_zero_exit(
    test_runner, provisioning_service
):
    provisioning_service.execute.return_value = AssemblyProvisioningResult(
        9606,
        "GRCh38",
        added=["GRCh37"],
        failed={"NCBI36": RuntimeError("no chain")},
    )
    result = test_runner.invoke(args=["assembly", "add", "--yes", "1"])
    assert result.exit_code != 0
    assert "Failed to provision NCBI36. no chain" in result.output
    assert "done with GRCh37" in result.output


def test_assembly_add_current_fails(test_runner, provisioning_service):
    provisioning_service.execute.side_effect = AssemblyProvisioningError(
        "Failed to set up current assembly 'GRCh38'. Error."
    )
    result = test_runner.invoke(args=["assembly", "add", "--yes", "1"])
    assert result.exit_code != 0
    assert "Failed to set up current assembly 'GRCh38'" in result.output


def test_assembly_add_no_such_assembly(test_runner, provisioning_service):
    provisioning_service.plan.side_effect = AssemblyNotFoundError("No assembly")
    result = test_runner.invoke(args=["assembly", "add", "--yes", "1"])
    assert result.exit_code != 0
    provisioning_service.execute.assert_not_called()

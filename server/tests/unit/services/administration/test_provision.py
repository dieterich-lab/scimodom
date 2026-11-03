import pytest
from sqlalchemy.exc import NoResultFound

from scimodom.services.administration.assembly.provision import (
    AssemblyProvisioningError,
    AssemblyProvisioningPlan,
    AssemblyProvisioningService,
)
from scimodom.services.assembly import AssemblyNotFoundError

PLAN = AssemblyProvisioningPlan(assembly_id=1, taxa_id=9606, assembly_name="GRCh38")


@pytest.fixture
def assembly_service(mocker):
    service = mocker.Mock()
    assembly = mocker.Mock(taxa_id=9606)
    assembly.id = 1
    assembly.name = "GRCh38"
    service.get_by_id.return_value = assembly
    service.get_coord_system_versions.return_value = ["GRCh38", "GRCh37", "NCBI36"]
    return service


def test_plan(assembly_service):
    plan = AssemblyProvisioningService(assembly_service).plan(1)
    assert plan == PLAN
    assembly_service.create_current.assert_not_called()


def test_plan_no_such_assembly(assembly_service):
    assembly_service.get_by_id.side_effect = NoResultFound
    with pytest.raises(AssemblyNotFoundError):
        AssemblyProvisioningService(assembly_service).plan(1)


def test_execute(mocker, assembly_service):
    result = AssemblyProvisioningService(assembly_service).execute(PLAN)
    assembly_service.create_current.assert_called_once_with(
        assembly_service.get_by_id.return_value
    )
    # the current assembly is not added again
    assert assembly_service.add_assembly.call_args_list == [
        mocker.call(9606, "GRCh37"),
        mocker.call(9606, "NCBI36"),
    ]
    assert result.current_assembly_name == "GRCh38"
    assert result.added == ["GRCh37", "NCBI36"]
    assert result.failed == {}
    assert result.is_complete


def test_execute_current_fails(assembly_service):
    failure = RuntimeError("download failed")
    assembly_service.create_current.side_effect = failure
    with pytest.raises(AssemblyProvisioningError) as exc:
        AssemblyProvisioningService(assembly_service).execute(PLAN)
    assert str(exc.value) == (
        "Failed to provision current assembly 'GRCh38'. download failed"
    )
    assert exc.value.__cause__ is failure
    # nothing else is attempted
    assembly_service.get_coord_system_versions.assert_not_called()
    assembly_service.add_assembly.assert_not_called()


def test_execute_other_assembly_fails(mocker, assembly_service):
    failure = RuntimeError("no chain file")
    assembly_service.add_assembly.side_effect = [failure, None]
    result = AssemblyProvisioningService(assembly_service).execute(PLAN)
    # all are attempted
    assert assembly_service.add_assembly.call_count == 2
    assert result.added == ["NCBI36"]
    assert result.failed == {"GRCh37": failure}
    assert not result.is_complete

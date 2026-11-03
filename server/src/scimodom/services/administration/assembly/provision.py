import logging
from dataclasses import dataclass, field
from functools import cache

from sqlalchemy.exc import NoResultFound

from scimodom.services.assembly import (
    AssemblyNotFoundError,
    AssemblyService,
    get_assembly_service,
)

logger = logging.getLogger(__name__)


class AssemblyProvisioningError(Exception):
    """Failed to provision current assembly; nothing else was attempted."""


@dataclass(frozen=True)
class AssemblyProvisioningPlan:
    """What will be provisioned (no side effects).

    NOTE: The other assemblies are only known once the current assembly
    exists (they are read from its info file).
    """

    assembly_id: int
    taxa_id: int
    assembly_name: str


@dataclass(frozen=True)
class AssemblyProvisioningResult:
    """What has been provisioned."""

    taxa_id: int
    current_assembly_name: str
    added: list[str] = field(default_factory=list)
    failed: dict[str, Exception] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Provisioning completed."""
        return not self.failed


class AssemblyProvisioningService:
    """Set up the assemblies for a given taxon.

    The current assembly is mandatory: if it fails, an
    AssemblyProvisioningError is raised and nothing else is attempted.
    The other assemblies (chain files to the current one) are
    all attempted and failures are reported in the result.
    Rerunning is safe, existing assemblies are skipped.

    :param assembly_service: Assembly service
    """

    def __init__(self, assembly_service: AssemblyService) -> None:
        self._assembly_service = assembly_service

    def plan(self, assembly_id: int) -> AssemblyProvisioningPlan:
        """Validate the current assembly (from the database).

        :param assembly_id: Assembly ID
        :raises AssemblyNotFoundError: If no such assembly
        :return: Plan
        """
        try:
            assembly = self._assembly_service.get_by_id(assembly_id)
        except NoResultFound as exc:
            raise AssemblyNotFoundError from exc
        return AssemblyProvisioningPlan(
            assembly.id,
            assembly.taxa_id,
            assembly.name,
        )

    def execute(
        self,
        plan: AssemblyProvisioningPlan,
    ) -> AssemblyProvisioningResult:
        """Set up the current assembly, then the others.

        :param plan: Plan
        :raises AssemblyProvisioningError: If the current assembly fails
        :return: Result, check 'failed' for assemblies that failed
        """
        assembly = self._assembly_service.get_by_id(plan.assembly_id)
        try:
            self._assembly_service.create_current(assembly)
        except Exception as exc:
            raise AssemblyProvisioningError(
                f"Failed to provision current assembly '{plan.assembly_name}'. {exc}"
            ) from exc

        added: list[str] = []
        failed: dict[str, Exception] = {}
        for name in self._assembly_service.get_coord_system_versions(plan.taxa_id):
            if name == plan.assembly_name:
                continue
            try:
                self._assembly_service.add_assembly(plan.taxa_id, name)
            except Exception as exc:
                logger.warning(f"Failed to provision assembly '{name}'.", exc_info=True)
                failed[name] = exc
            else:
                added.append(name)
        return AssemblyProvisioningResult(
            taxa_id=plan.taxa_id,
            current_assembly_name=plan.assembly_name,
            added=added,
            failed=failed,
        )


@cache
def get_assembly_provisioning_service() -> AssemblyProvisioningService:
    """Instantiate an AssemblyProvisioningService object by injecting its dependencies.

    :return: Assembly provisioning service instance
    """
    return AssemblyProvisioningService(assembly_service=get_assembly_service())

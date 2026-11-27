"""Classes and methods for assembly provisioning."""

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

    The other assemblies are only known once the current assembly
    exists (they are read from its manifest).
    """

    assembly_id: int
    taxa_id: int
    assembly_name: str
    release: int
    archive: str


@dataclass(frozen=True)
class AssemblyProvisioningResult:
    """What has been provisioned."""

    taxa_id: int
    current_assembly_name: str
    added: list[str] = field(default_factory=list)
    failed: dict[str, Exception] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Return provisioning status.

        :return: True if completed,
        False if failed
        """
        return not self.failed


class AssemblyProvisioningService:
    """Provide a utility class to set up assemblies.

    :param assembly_service: Assembly service
    """

    def __init__(self, assembly_service: AssemblyService) -> None:
        self._assembly_service = assembly_service

    def plan(
        self, taxa_id: int, release: int, archive: str
    ) -> AssemblyProvisioningPlan:
        """Resolve the current assembly for taxa_id.

        :param taxa_id: NCBI taxon
        :param release: Ensembl release to obtain the files from
        :param archive: Ensembl archive to obtain the files from
        :raise AssemblyNotFoundError: If no current assembly
        :return: Provisioning plan
        """
        try:
            assembly = self._assembly_service.get_current(taxa_id)
        except NoResultFound as exc:
            raise AssemblyNotFoundError from exc
        return AssemblyProvisioningPlan(
            assembly.id,
            assembly.taxa_id,
            assembly.name,
            release,
            archive,
        )

    def execute(
        self,
        plan: AssemblyProvisioningPlan,
    ) -> AssemblyProvisioningResult:
        """Set up the current assembly, then the others.

        If the current assembly fails, nothing else is attempted.
        The other assemblies (chain files to the current one) are
        all attempted and failures are reported in the result.
        Existing assemblies are skipped.

        :param plan: Plan
        :raise AssemblyProvisioningError: If the current assembly fails
        :return: Provisioning result
        """
        assembly = self._assembly_service.get_by_id(plan.assembly_id)
        try:
            self._assembly_service.create_current(
                assembly,
                plan.release,
                plan.archive,
            )
        except Exception as exc:
            raise AssemblyProvisioningError(
                f"Failed to provision current assembly '{assembly.name}'. {exc}"
            ) from exc

        added: list[str] = []
        failed: dict[str, Exception] = {}
        for name in self._assembly_service.get_coord_system_versions(
            plan.taxa_id,
        ):
            if name == plan.assembly_name:
                continue
            try:
                self._assembly_service.add_assembly(plan.taxa_id, name)
            except Exception as exc:
                logger.warning(
                    f"Failed to provision assembly '{name}'.",
                    exc_info=True,
                )
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
    """Instantiate an AssemblyProvisioningService.

    :return: Assembly provisioning service instance
    """
    return AssemblyProvisioningService(assembly_service=get_assembly_service())

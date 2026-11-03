import logging
from dataclasses import dataclass, field
from functools import cache


from scimodom.services.dataset import DatasetService, get_dataset_service
from scimodom.services.project import ProjectService, get_project_service
from scimodom.services.selection import SelectionService, get_selection_service

logger = logging.getLogger(__name__)


class ProjectDeletionError(Exception):
    """Deletion failed.

    The deletion can be resumed by planning and executing it again.

    :param message: Description
    :param deleted_dataset_ids: Datasets deleted before the failure
    :param remaining_dataset_ids: Datasets (of the project) not deleted
    """

    def __init__(
        self,
        message: str,
        deleted_dataset_ids: list[str],
        remaining_dataset_ids: list[str],
    ) -> None:
        super().__init__(message)
        self.deleted_dataset_ids = deleted_dataset_ids
        self.remaining_dataset_ids = remaining_dataset_ids


@dataclass(frozen=True)
class DatasetSummary:
    """Summary of datasets included in this project."""

    id: str
    title: str


@dataclass(frozen=True)
class ProjectDeletionPlan:
    """What a deletion will remove. Has no side effects."""

    project_id: str
    title: str
    datasets: list[DatasetSummary] = field(default_factory=list)


@dataclass(frozen=True)
class ProjectDeletionResult:
    """Deletion outcome."""

    project_id: str
    deleted_dataset_ids: list[str] = field(default_factory=list)


class ProjectDeletionService:
    """Delete a project and all associated data.

    Datasets (and their selections, data, BAM files...) are deleted one
    by one, each in its own transaction, and the project last. If a
    step fails, what was already deleted stays deleted, and the
    operation can simply be repeated: it resumes with the remaining
    datasets.

    :param project_service: Project service
    :param dataset_service: Dataset service
    :param selection_service: Selection service
    """

    def __init__(
        self,
        project_service: ProjectService,
        dataset_service: DatasetService,
        selection_service: SelectionService,
    ) -> None:
        self._project_service = project_service
        self._dataset_service = dataset_service
        self._selection_service = selection_service

    def plan(self, project_id: str) -> ProjectDeletionPlan:
        """Describe what deleting a project would remove.

        :param project_id: Project SMID
        :raises NoResultFound: If no such project
        :return: Plan
        """
        project = self._project_service.get_by_id(project_id)
        return ProjectDeletionPlan(
            project_id=project.id,
            title=project.title,
            datasets=[DatasetSummary(d.id, d.title) for d in project.datasets],
        )

    def execute(self, plan: ProjectDeletionPlan) -> ProjectDeletionResult:
        """Delete the project and its datasets.

        The project is read again, i.e. what is deleted is what exists
        now, not necessarily what the plan listed.

        :param plan: Plan
        :type plan: ProjectDeletionPlan
        :raises NoResultFound: If the project no longer exists
        :raises ProjectDeletionError: If a dataset or the project could
        not be deleted. The exception states what was deleted.
        :returns: Result
        :rtype: ProjectDeletionResult
        """
        project = self._project_service.get_by_id(plan.project_id)
        pending = [dataset.id for dataset in project.datasets]
        deleted: list[str] = []
        for dataset in list(project.datasets):
            try:
                self._selection_service.delete_selections_by_dataset(dataset)
                self._dataset_service.delete_dataset(dataset)
            except Exception as exc:
                raise ProjectDeletionError(
                    f"Failure in handling Dataset '{dataset.id}'. "
                    f"Datasets '{','.join(pending)}' were not deleted.",
                    deleted_dataset_ids=deleted,
                    remaining_dataset_ids=pending,
                ) from exc
            deleted.append(dataset.id)
            pending.remove(dataset.id)
            logger.info(f"Deleted dataset '{dataset.id}'.")

        try:
            self._project_service.delete_project(project)
        except Exception as exc:
            raise ProjectDeletionError(
                f"Failed to delete project '{plan.project_id}' "
                "(all its datasets were deleted).",
                deleted_dataset_ids=deleted,
                remaining_dataset_ids=[],
            ) from exc
        return ProjectDeletionResult(plan.project_id, deleted)


@cache
def get_project_deletion_service() -> ProjectDeletionService:
    """Instantiate a ProjectDeletionService object by injecting its dependencies.

    :return: Project deletion service instance
    """
    return ProjectDeletionService(
        project_service=get_project_service(),
        dataset_service=get_dataset_service(),
        selection_service=get_selection_service(),
    )

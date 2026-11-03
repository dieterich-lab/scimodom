import csv
import os
import re
import datetime
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Iterator

from sqlalchemy.exc import NoResultFound

from scimodom.services.assembly import (
    AssemblyNotFoundError,
    AssemblyService,
    get_assembly_service,
)
from scimodom.services.dataset import DatasetService, get_dataset_service
from scimodom.services.file import FileService, get_file_service
from scimodom.services.permission import PermissionService, get_permission_service
from scimodom.services.project import ProjectService, get_project_service
from scimodom.services.user import NoSuchUser, UserService, get_user_service
from scimodom.services.utilities import UtilitiesService, get_utilities_service
from scimodom.utils.specs.enums import AnnotationSource
from scimodom.utils.dtos.project import (
    ProjectMetaDataDto,
    ProjectOrganismDto,
    ProjectSourceDto,
    ProjectTemplate,
)


_NOTE_PATTERN = re.compile(r"(?:file=)(?P<file>.*),\s*(?:title=)(?P<title>.*)")


class ProjectTemplateError(Exception):
    """A project template (or its source) is missing or invalid."""


class UserAssociationError(Exception):
    """The project was created, but the user could not be added to it.

    :param message: Description
    :param project_id: SMID of the created project
    """

    def __init__(self, message: str, project_id: str) -> None:
        super().__init__(message)
        self.project_id = project_id


@dataclass(frozen=True)
class ProjectRequestInfo:
    """Project level information for a new template."""

    title: str
    summary: str
    surname: str
    forename: str
    institution: str
    email: str
    published: datetime.date | None = None
    doi: tuple[str, ...] = ()
    pmid: tuple[int, ...] = ()


@dataclass(frozen=True)
class ProjectIngestionResult:
    """Result of creating a project.

    :param project_id: SMID
    :param user_added: None if no user was requested, True if the
    contact was added (or already associated), False if there is no
    such user.
    """

    project_id: str
    user_added: bool | None = None


def parse_dataset_note(note: str | None) -> tuple[str, str]:
    """Get the dataset file name and title from a metadata note.

    :param note: Note with format 'file=filename.bedrmod, title=title'
    :raises ProjectTemplateError: If the note does not have this format
    :return: File name and title
    """
    if note is None:
        raise ProjectTemplateError(
            "'note' must be str with format 'file=filename.bedrmod, title=title'"
        )
    match = _NOTE_PATTERN.match(note)
    if match is None:
        raise ProjectTemplateError("Unable to match 'file' or 'title' from 'note'.")
    return match["file"].strip(), match["title"].strip()


@dataclass(frozen=True)
class BatchDataset:
    """A dataset to import: one file, one or more modifications.

    :param modifications: (RNA type, MODOMICS ID) for each modification
    """

    file_path: Path
    title: str
    assembly_id: int
    taxa_id: int
    cto: str
    method_id: str
    tech: str
    modifications: tuple[tuple[str, str], ...]

    @property
    def filename(self) -> str:
        return self.file_path.name


@dataclass(frozen=True)
class BatchImportPlan:
    """A validated batch import (no side effects)."""

    request_uuid: str
    template: ProjectTemplate
    datasets: list[BatchDataset]


@dataclass(frozen=True)
class BatchDatasetOutcome:
    """Outcome of importing one dataset."""

    dataset: BatchDataset
    dataset_id: str | None = None
    error: Exception | None = None

    @property
    def is_imported(self) -> bool:
        return self.error is None


class ProjectIngestionService:
    """Project administration and ingestion.

    :param project_service: Project service
    :param assembly_service: Assembly service
    :param utilities_service: Utilities service
    :param file_service: File service
    :param permission_service: Permission service
    :param user_service: User service
    :param dataset_service: Dataset service
    """

    def __init__(
        self,
        project_service: ProjectService,
        assembly_service: AssemblyService,
        utilities_service: UtilitiesService,
        file_service: FileService,
        permission_service: PermissionService,
        user_service: UserService,
        dataset_service: DatasetService,
    ) -> None:
        self._project_service = project_service
        self._assembly_service = assembly_service
        self._utilities_service = utilities_service
        self._file_service = file_service
        self._permission_service = permission_service
        self._user_service = user_service
        self._dataset_service = dataset_service

    # project request (template)

    def build_template(
        self,
        dataset_csv: str | Path,
        info: ProjectRequestInfo,
        use_mod_ids: bool = False,
        use_method_ids: bool = False,
    ) -> ProjectTemplate:
        """Build a project template from a CSV file of datasets.

        Nothing is written.

        :param dataset_csv: Path to CSV with row-wise dataset metadata
        :param info: Project information
        :param use_mod_ids: Use modification IDs as given, do not infer them
        :param use_method_ids: Use method IDs as given, do not infer them
        :raises ProjectTemplateError: If the CSV cannot be read, is
        malformed, or has unexpected values.
        :return: Valid project template
        """
        try:
            metadata = self._read_metadata(dataset_csv, use_mod_ids, use_method_ids)
            return ProjectTemplate(
                title=info.title,
                summary=info.summary,
                contact_name=f"{info.surname}, {info.forename}",
                contact_institution=info.institution,
                contact_email=info.email,
                date_published=info.published,
                external_sources=self._get_sources(info.doi, info.pmid),
                metadata=metadata,
            )
        except KeyError as exc:
            raise ProjectTemplateError(
                f"Malformed DATASET_CSV. Missing header {exc}"
            ) from exc
        except (NoResultFound, ValueError) as exc:  # includes ValidationError
            raise ProjectTemplateError(
                f"DATASET_CSV has unexpected values. {exc}"
            ) from exc
        except OSError as exc:
            raise ProjectTemplateError(f"Cannot read DATASET_CSV. {exc}") from exc

    def save_request(self, template: ProjectTemplate) -> str:
        """Write a project request (template) to the file system.

        :param template: Valid template
        :return: Request UUID
        """
        return self._project_service.create_project_request(template)

    def load_template(self, request_uuid: str) -> ProjectTemplate:
        """Read a project request and make sure it can be used.

        Assembly IDs missing from the template are filled in from
        the database, they are not created.

        :param request_uuid: Request UUID
        :raises ProjectTemplateError: If the request cannot be
        read or validated.
        :raises AssemblyNotFoundError: If an assembly does not exist.
        :return: Valid project template
        """
        try:
            with self._file_service.open_project_request_file(request_uuid) as fh:
                template = ProjectTemplate.model_validate_json(fh.read())
        except Exception as exc:  # OSError, ValidationError
            raise ProjectTemplateError(f"Failed to read template. {exc}") from exc
        self.assign_assembly_ids(template)
        return template

    def assign_assembly_ids(self, template: ProjectTemplate) -> None:
        """Set the assembly ID in the template where it is None.

        If an ID is given, check that it exists.

        :param template: Project template, modified in place
        :raises AssemblyNotFoundError: If an assembly does not exist.
        """
        for metadata in template.metadata:
            organism = metadata.organism
            try:
                if organism.assembly_id is None:
                    assembly = self._assembly_service.get_by_taxa_and_name(
                        organism.taxa_id, organism.assembly_name
                    )
                    organism.assembly_id = assembly.id
                else:
                    self._assembly_service.get_by_id(organism.assembly_id)
            except NoResultFound as exc:
                raise AssemblyNotFoundError(
                    f"No such assembly '{organism.assembly_name}' "
                    f"for organism '{organism.taxa_id}'"
                ) from exc

    # project

    def create_project(
        self,
        template: ProjectTemplate,
        request_uuid: str,
        add_user: bool = False,
    ) -> ProjectIngestionResult:
        """Create a project from a template.

        :param template: Valid template (cf. load_template)
        :param request_uuid: Request UUID
        :param add_user: Associate the project contact
        (email) with the project, if this user exists.
        :raises Exception: If the project cannot be created
        (nothing is created).
        :raises UserAssociationError: If the project was created, but
        the user could not be added.
        :return: Result
        """
        project_id = self._project_service.create_project(template, request_uuid)
        if not add_user:
            return ProjectIngestionResult(project_id)
        try:
            self.add_user_to_project(template.contact_email, project_id)
        except NoSuchUser:
            return ProjectIngestionResult(project_id, user_added=False)
        except Exception as exc:
            raise UserAssociationError(
                f"Project '{project_id}' was created, but failed to add user. {exc}",
                project_id,
            ) from exc
        return ProjectIngestionResult(project_id, user_added=True)

    def add_user_to_project(self, username: str, project_id: str) -> None:
        """Associate a user with a project, if not already.

        :param username: User email
        :param project_id: Project SMID
        :raises NoResultFound: If no such project
        :raises NoSuchUser: If no such user
        """
        self._project_service.get_by_id(project_id)
        user = self._user_service.get_user_by_email(username)
        self._permission_service.insert_into_user_project_association(user, project_id)

    # batch import (project and datasets)

    def plan_batch_import(
        self, input_directory: str | Path, request_uuid: str
    ) -> BatchImportPlan:
        """Validate a batch import of a project and all its datasets.

        The 'note' of each metadata entry must contain the dataset file
        name and title, 'file=filename.bedrmod, title=title'. Entries
        with the same file name are modifications of the same dataset
        and must agree on title, assembly, organism, and technology.
        All files must exist under the input directory.

        :param input_directory: Directory with the bedRMod (EU-formatted) files
        :param request_uuid: Request UUID (project template)
        :raises ProjectTemplateError: If the template, or any of the
        datasets, is invalid.
        :raises AssemblyNotFoundError: If an assembly does not exist.
        :return: Plan
        """
        template = self.load_template(request_uuid)
        problems: list[str] = []
        entries: dict[str, dict] = {}
        for index, metadata in enumerate(template.metadata, start=1):
            try:
                filename, title = parse_dataset_note(metadata.note)
            except ProjectTemplateError as exc:
                problems.append(f"Metadata entry {index}: {exc}")
                continue
            organism = metadata.organism
            key = (
                title,
                organism.assembly_id,
                organism.taxa_id,
                organism.cto,
                metadata.method_id,
                metadata.tech,
            )
            entry = entries.setdefault(filename, {"key": key, "modifications": []})
            if entry["key"] != key:
                problems.append(
                    f"Metadata entry {index}: file '{filename}' is repeated "
                    "with a different title, assembly, organism or technology."
                )
            entry["modifications"].append((metadata.rna, metadata.modomics_id))

        parent = Path(input_directory).resolve()
        datasets = []
        for filename, entry in entries.items():
            file_path = (parent / filename).resolve()
            if not file_path.is_relative_to(parent):
                problems.append(f"File '{filename}' is not under the input directory.")
            elif not file_path.is_file():
                problems.append(f"File '{filename}' not found in '{input_directory}'.")
            else:
                title, assembly_id, taxa_id, cto, method_id, tech = entry["key"]
                datasets.append(
                    BatchDataset(
                        file_path=file_path,
                        title=title,
                        assembly_id=assembly_id,
                        taxa_id=taxa_id,
                        cto=cto,
                        method_id=method_id,
                        tech=tech,
                        modifications=tuple(entry["modifications"]),
                    )
                )
        if problems:
            raise ProjectTemplateError(
                "Invalid batch import:\n" + "\n".join(f"  - {p}" for p in problems)
            )
        return BatchImportPlan(request_uuid, template, datasets)

    def import_batch_datasets(
        self,
        plan: BatchImportPlan,
        project_id: str,
        annotation_source: AnnotationSource,
    ) -> Iterator[BatchDatasetOutcome]:
        """Import the datasets of a plan into an existing project.

        This is a generator: A dataset that fails is reported in its
        outcome, and does not prevent the others from being imported.

        :param plan: Plan
        :param project_id: Project SMID
        :param annotation_source: Annotation source (the same for all datasets)
        :return: Outcomes, in the order of the plan
        """
        for dataset in plan.datasets:
            try:
                dataset_id = self._import_batch_dataset(
                    dataset, project_id, annotation_source
                )
            except Exception as exc:
                yield BatchDatasetOutcome(dataset, error=exc)
            else:
                yield BatchDatasetOutcome(dataset, dataset_id=dataset_id)

    def _import_batch_dataset(
        self,
        dataset: BatchDataset,
        project_id: str,
        annotation_source: AnnotationSource,
    ) -> str:
        # selections (modification, organism, technology) exist once
        # the project is created, so their IDs are only known now
        modification_ids = [
            self._utilities_service.get_modification_id(rna, modomics_id)
            for rna, modomics_id in dataset.modifications
        ]
        organism_id = self._utilities_service.get_organism_id(
            dataset.taxa_id, dataset.cto
        )
        technology_id = self._utilities_service.get_technology_id(
            dataset.method_id, dataset.tech
        )
        with open(dataset.file_path) as fp:
            return self._dataset_service.import_dataset(
                fp,
                source=dataset.file_path.as_posix(),
                project_id=project_id,
                title=dataset.title,
                assembly_id=dataset.assembly_id,
                modification_ids=modification_ids,
                organism_id=organism_id,
                technology_id=technology_id,
                annotation_source=annotation_source,
            )

    # helpers

    def _read_metadata(
        self, dataset_csv: str | Path, use_mod_ids: bool, use_method_ids: bool
    ) -> list[ProjectMetaDataDto]:
        with open(dataset_csv, "r", newline="") as fh:
            rows = [
                {
                    k.strip(): (v.strip() if isinstance(v, str) else v)
                    for k, v in row.items()
                }
                for row in csv.DictReader(fh)
            ]
        return [self._get_metadata(row, use_mod_ids, use_method_ids) for row in rows]

    def _get_metadata(
        self, row: dict, use_mod_ids: bool, use_method_ids: bool
    ) -> ProjectMetaDataDto:
        organism = ProjectOrganismDto(
            taxa_id=row["taxa_id"],
            cto=row["cto"],
            assembly_name=row["assembly"],
            assembly_id=row["assembly_id"] if "assembly_id" in row else None,
        )
        return ProjectMetaDataDto(
            rna=row["rna_type"],
            modomics_id=(
                row["modification"]
                if use_mod_ids
                else self._utilities_service.get_modomics_id_by_short_name(
                    row["modification"]
                )
            ),
            tech=row["technology"],
            method_id=(
                row["method"]
                if use_method_ids
                else self._utilities_service.get_method_id_by_name(row["method"])
            ),
            organism=organism,
            note=(
                row["note"]
                if "note" in row
                else f'file={row["file"]}, title={row["title"]}'
            ),
        )

    @staticmethod
    def _get_sources(
        doi: tuple[str, ...] | list[str], pmid: tuple[int, ...] | list[int]
    ) -> list[ProjectSourceDto]:
        # 'null' stands for a PMID without DOI, 0 for a DOI without PMID
        return [
            ProjectSourceDto(
                doi=None if dv == "null" else dv,
                pmid=None if pv == 0 else pv,
            )
            for dv, pv in zip(doi, pmid)
        ]


@cache
def get_project_ingestion_service() -> ProjectIngestionService:
    """Instantiate a ProjectIngestionService object by injecting its dependencies.

    :return: Project ingestion service instance
    """
    return ProjectIngestionService(
        project_service=get_project_service(),
        assembly_service=get_assembly_service(),
        utilities_service=get_utilities_service(),
        file_service=get_file_service(),
        permission_service=get_permission_service(),
        user_service=get_user_service(),
        dataset_service=get_dataset_service(),
    )

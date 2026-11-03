import csv
import datetime
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from sqlalchemy.exc import NoResultFound

from scimodom.services.assembly import (
    AssemblyNotFoundError,
    AssemblyService,
    get_assembly_service,
)
from scimodom.services.file import FileService, get_file_service
from scimodom.services.permission import PermissionService, get_permission_service
from scimodom.services.project import ProjectService, get_project_service
from scimodom.services.user import NoSuchUser, UserService, get_user_service
from scimodom.services.utilities import UtilitiesService, get_utilities_service
from scimodom.utils.dtos.project import (
    ProjectMetaDataDto,
    ProjectOrganismDto,
    ProjectSourceDto,
    ProjectTemplate,
)


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


class ProjectIngestionService:
    """Project administration and ingestion.

    :param project_service: Project service
    :param assembly_service: Assembly service
    :param utilities_service: Utilities service
    :param file_service: File service
    :param permission_service: Permission service
    :param user_service: User service
    """

    def __init__(
        self,
        project_service: ProjectService,
        assembly_service: AssemblyService,
        utilities_service: UtilitiesService,
        file_service: FileService,
        permission_service: PermissionService,
        user_service: UserService,
    ) -> None:
        self._project_service = project_service
        self._assembly_service = assembly_service
        self._utilities_service = utilities_service
        self._file_service = file_service
        self._permission_service = permission_service
        self._user_service = user_service

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
    )

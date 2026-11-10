from datetime import datetime, timezone
import logging
from functools import cache
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import tuple_, and_, or_, select, func, delete

from scimodom.database.database import get_session
from scimodom.database.models import (
    Project,
    ProjectSource,
    ProjectContact,
    ProjectSelection,
    User,
    UserProjectAssociation,
)
from scimodom.services.file import FileService, get_file_service
from scimodom.services.selection import SelectionService, get_selection_service
from scimodom.utils.dtos.project import ProjectTemplate
from scimodom.utils.specs.enums import Identifiers
from scimodom.utils.utils import gen_short_uuid

logger = logging.getLogger(__name__)


class DuplicateProjectError(Exception):
    """Exception handling for duplicate projects."""

    pass


class ProjectService:
    def __init__(
        self,
        session: Session,
        file_service: FileService,
        selection_service: SelectionService,
    ) -> None:
        self._session = session
        self._file_service = file_service
        self._selection_service = selection_service

    def create_project_request(self, project_template: ProjectTemplate) -> str:
        """Provide a project request constructor.

        :param project_template: Validated project template
        :type project_template: ProjectTemplate
        :return: UUID of request
        :rtype: str
        """
        uuid = gen_short_uuid(22, [])
        with self._file_service.create_project_request_file(uuid) as fp:
            fp.write(project_template.model_dump_json(indent=4))
        return uuid

    def get_by_id(self, project_id: str) -> Project:
        """Retrieve project by SMID.

        :param project_id: SMID
        :type project_id: str
        :return: Project
        :rtype: Project
        """
        return self._session.get_one(Project, project_id)

    def get_projects(self, user: User | None = None) -> list[dict[str, Any]]:
        """Retrieve all projects.

        :param user: Optionally restricts the
        results based on projects associated with a user.
        :type user: User
        :return: Query result
        :rtype: list of dict
        """
        query = (
            select(
                Project.id.label("project_id"),
                Project.title.label("project_title"),
                Project.summary.label("project_summary"),
                Project.date_added,
                Project.date_published,
                ProjectContact.contact_name,
                ProjectContact.contact_institution,
                func.group_concat(ProjectSource.doi.distinct()).label("doi"),
                func.group_concat(ProjectSource.pmid.distinct()).label("pmid"),
            )
            .join_from(Project, ProjectContact, Project.inst_contact)
            .join_from(Project, ProjectSource, Project.sources, isouter=True)
        )
        if user is not None:
            query = (
                query.join(
                    UserProjectAssociation,
                    UserProjectAssociation.project_id == Project.id,
                )
                .join(User, User.id == UserProjectAssociation.user_id)
                .where(User.id == user.id)
            )
        query = query.group_by(Project.id)
        return [row._asdict() for row in self._session.execute(query)]

    def create_project(
        self, project_template: ProjectTemplate, request_uuid: str
    ) -> str:
        """Provide a project constructor.

        :param project_template: Validated project template
        :param request_uuid: UUID of request (original template)
        :raises Exception: If fail to create project
        :return: Newly created project SMID
        """
        project_id = None
        metadata_written = False
        try:
            self._validate_entry(project_template)
            project_id = self._add_project(project_template)
            self._selection_service.add_project_selections(
                project_id, project_template.metadata, is_flush_only=True
            )
            self._write_project_metadata(project_template, project_id)
            metadata_written = True
            self._session.commit()
        except Exception:
            self._session.rollback()
            if metadata_written:
                self._discard_project_metadata(project_id)
            raise
        self._discard_request(request_uuid)
        return project_id

    def delete_project(self, project: Project) -> None:
        """Delete a project and all associated data.

        NOTE: There must be no conflicting FK constraints
        (not using ON DELETE CASCADE), i.e. dataset and
        associated data must first be deleted by the caller.

        Delete from the following tables:
        - project_source
        - project_selection
        - user_project_association
        - project
        - project_contact

        :param project_id: Project instance
        :raises Exception: If fail to delete project, project source,
        project contact, or user project association.
        """
        project_id = project.id
        try:
            self._session.execute(
                delete(ProjectSource).filter_by(project_id=project_id)
            )
            self._session.execute(
                delete(ProjectSelection).filter_by(project_id=project_id)
            )
            self._session.execute(
                delete(UserProjectAssociation).filter_by(project_id=project_id)
            )
            contact = self._session.get_one(ProjectContact, project.contact_id)
            projects = contact.projects
            if len(projects) == 1 and projects[0].id == project_id:
                self._session.delete(contact)
            self._session.delete(project)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        self._discard_project_metadata(project_id)

    @staticmethod
    def _get_prj_src(project_template: ProjectTemplate):
        ors = or_(False)
        ands = and_(True)

        if project_template.external_sources:
            for source in project_template.external_sources:
                doi = source.doi
                pmid = source.pmid
                if doi is None:
                    if pmid is not None:
                        ands = and_(
                            ProjectSource.doi.is_(None), ProjectSource.pmid.in_([pmid])
                        )
                    # else:
                    # ands = and_(ProjectSource.doi.is_(None), ProjectSource.pmid.is_(None))
                elif pmid is None:
                    ands = and_(
                        ProjectSource.doi.in_([doi]), ProjectSource.pmid.is_(None)
                    )
                else:
                    ands = tuple_(ProjectSource.doi, ProjectSource.pmid).in_(
                        [tuple([doi, pmid])]
                    )
                ors = or_(ors, ands)
        else:
            ors = ands  # if no sources
        return ors

    def _validate_entry(self, project_template: ProjectTemplate) -> None:
        query = (
            select(func.distinct(Project.id))
            .join_from(Project, ProjectSource, Project.sources, isouter=True)
            .where(Project.title == project_template.title)
        )
        query = query.where(self._get_prj_src(project_template))
        project_id = self._session.execute(query).scalar_one_or_none()
        if project_id:
            raise DuplicateProjectError(
                f"Suspected duplicate project with SMID '{project_id}' and title '{project_template.title}'."
            )

    def _add_contact_if_none(self, project_template: ProjectTemplate) -> int:
        contact_id = self._session.execute(
            select(ProjectContact.id).filter_by(
                contact_name=project_template.contact_name,
                contact_institution=project_template.contact_institution,
                contact_email=project_template.contact_email,
            )
        ).scalar_one_or_none()
        if not contact_id:
            contact = ProjectContact(
                contact_name=project_template.contact_name,
                contact_institution=project_template.contact_institution,
                contact_email=project_template.contact_email,
            )
            self._session.add(contact)
            self._session.flush()
            contact_id = contact.id
        return contact_id

    def _add_project(self, project_template: ProjectTemplate) -> str:
        project_ids = self._session.execute(select(Project.id)).scalars().all()
        project_id = gen_short_uuid(Identifiers.SMID.length, project_ids)
        contact_id = self._add_contact_if_none(project_template)
        stamp = datetime.now(timezone.utc)  # .isoformat()
        project = Project(
            id=project_id,
            title=project_template.title,
            summary=project_template.summary,
            contact_id=contact_id,
            date_published=project_template.date_published,
            date_added=stamp,
        )
        sources = []
        for source_dto in project_template.external_sources:
            source = ProjectSource(
                project_id=project_id, doi=source_dto.doi, pmid=source_dto.pmid
            )
            sources.append(source)

        logger.info(f"Adding project_template {project_id}...")

        self._session.add(project)
        self._session.add_all(sources)
        self._session.flush()
        return project_id

    def _write_project_metadata(
        self, project_template: ProjectTemplate, project_id: str
    ) -> None:
        # raises FileExistsError if the file exists
        fh = self._file_service.create_project_metadata_file(project_id)
        try:
            with fh:
                fh.write(project_template.model_dump_json(indent=4))
        except Exception:
            self._discard_project_metadata(project_id)
            raise

    def _discard_project_metadata(self, project_id: str) -> None:
        # clean-up, must not raise: either after a failure (do not mask
        # the original error), or after a commit (the data is committed)
        try:
            self._file_service.delete_project_metadata_file(project_id)
        except FileNotFoundError:
            pass
        except Exception as exc:
            logger.warning(f"Failed to delete metadata file for '{project_id}': {exc}")

    def _discard_request(self, request_uuid: str) -> None:
        try:
            self._file_service.delete_project_request_file(request_uuid)
        except Exception as exc:
            logger.warning(f"Failed to delete project request '{request_uuid}': {exc}")


@cache
def get_project_service():
    """Instantiate a ProjectService object by injecting its dependencies.

    :returns: Project service instance
    :rtype: ProjectService
    """
    return ProjectService(
        session=get_session(),
        file_service=get_file_service(),
        selection_service=get_selection_service(),
    )

from datetime import datetime, timezone
import logging
from functools import cache
from pathlib import Path
from typing import ClassVar

from sqlalchemy.orm import Session
from sqlalchemy import tuple_, and_, or_, select, func

from scimodom.config import Config
from scimodom.database.database import get_session
from scimodom.database.models import (
    Project,
    ProjectSource,
    ProjectContact,
    Modification,
    DetectionTechnology,
    Organism,
    Selection,
    User,
    UserProjectAssociation,
)
from scimodom.utils.project_dto import ProjectTemplate, ProjectMetaDataDto
from scimodom.utils.specifications import SMID_LENGTH
from scimodom.utils.utils import gen_short_uuid

logger = logging.getLogger(__name__)


class DuplicateProjectError(Exception):
    """Exception handling for duplicate projects."""

    pass


class ProjectService:
    DATA_PATH: ClassVar[str | Path] = Config.DATA_PATH
    METADATA_PATH: ClassVar[str] = "metadata"
    REQUEST_PATH: ClassVar[str] = "project_requests"

    def __init__(self, session: Session) -> None:
        self._session = session

    def __new__(cls, session: Session, **kwargs):
        if cls.DATA_PATH is None:
            msg = "Missing environment variable: DATA_PATH."
            raise ValueError(msg)
        elif not Path(cls.DATA_PATH, cls.METADATA_PATH).is_dir():
            msg = f"No such directory '{Path(cls.DATA_PATH, cls.METADATA_PATH)}'."
            raise FileNotFoundError(msg)
        elif not Path(cls.DATA_PATH, cls.METADATA_PATH, cls.REQUEST_PATH).is_dir():
            msg = f"No such directory '{Path(cls.DATA_PATH, cls.METADATA_PATH, cls.REQUEST_PATH)}'."
            raise FileNotFoundError(msg)
        else:
            return super().__new__(cls)

    @staticmethod
    def create_project_request(project_template: ProjectTemplate) -> str:
        """Project request constructor.

        :param project_template: Validated project template
        :type project_template: ProjectTemplate
        :returns: UUID of request
        :rtype: str
        """
        project_request_path = Path(
            ProjectService.DATA_PATH,
            ProjectService.METADATA_PATH,
            ProjectService.REQUEST_PATH,
        )

        uuid = gen_short_uuid(24, [])
        filen = Path(project_request_path, f"{uuid}.json")

        logger.info(f"Writing project request to {filen}...")

        with open(filen, "w") as f:
            f.write(project_template.model_dump_json(indent=4))
        return uuid

    def get_by_id(self, smid: str) -> Project:
        """Retrieve project by SMID

        :param smid: SMID
        :type smid: str
        """
        return self._session.get_one(Project, smid)

    def get_projects(self, user: User | None = None) -> list[dict[str, any]]:
        """Retrieve all projects.

        :param user: Optionally restricts the
        results based on projects assotiated with a user.
        :type user: User
        :returns: Query result
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
        """Project constructor.

        :param project: Validated project template
        :type project: ProjectTemplate
        :param request_uuid: UUID of request (original template)
        :type request_uuid: str
        :returns: Newly created project SMID
        :rtype: str
        """
        try:
            self._validate_entry(project_template)
            self._add_selection_if_none(project_template)
            smid = self._add_project(project_template)
            self._write_project_template(project_template, smid, request_uuid)
            self._session.commit()
            return smid
        except:
            self._session.rollback()
            raise

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
        smid = self._session.execute(query).scalar_one_or_none()
        if smid:
            raise DuplicateProjectError(
                f"Suspected duplicate project with SMID '{smid}' and title '{project_template.title}'."
            )

    def _add_selection_if_none(self, project_template: ProjectTemplate) -> None:
        # no upsert, add only if on_conflict_do_nothing?
        for metadata in project_template.metadata:
            modification_id = self._add_modification_if_none(metadata)
            organism_id = self._add_organism_if_none(metadata)
            technology_id = self._add_technology_if_none(metadata)
            selection_id = self._session.execute(
                select(Selection.id).filter_by(
                    modification_id=modification_id,
                    organism_id=organism_id,
                    technology_id=technology_id,
                )
            ).scalar_one_or_none()
            if not selection_id:
                logger.info(
                    f"Adding selection ID ({modification_id}, {organism_id}, {technology_id})"
                )
                selection = Selection(
                    modification_id=modification_id,
                    organism_id=organism_id,
                    technology_id=technology_id,
                )
                self._session.add(selection)
                self._session.flush()

    def _add_modification_if_none(self, metadata: ProjectMetaDataDto) -> int:
        modification_id = self._session.execute(
            select(Modification.id).filter_by(
                rna=metadata.rna, modomics_id=metadata.modomics_id
            )
        ).scalar_one_or_none()
        if not modification_id:
            modification = Modification(
                rna=metadata.rna, modomics_id=metadata.modomics_id
            )
            self._session.add(modification)
            self._session.flush()
            modification_id = modification.id
        return modification_id

    def _add_organism_if_none(self, metadata: ProjectMetaDataDto) -> int:
        organism_id = self._session.execute(
            select(Organism.id).filter_by(
                cto=metadata.organism.cto, taxa_id=metadata.organism.taxa_id
            )
        ).scalar_one_or_none()
        if not organism_id:
            organism = Organism(
                cto=metadata.organism.cto, taxa_id=metadata.organism.taxa_id
            )
            self._session.add(organism)
            self._session.flush()
            organism_id = organism.id
        return organism_id

    def _add_technology_if_none(self, metadata: ProjectMetaDataDto) -> int:
        technology_id = self._session.execute(
            select(DetectionTechnology.id).filter_by(
                tech=metadata.tech, method_id=metadata.method_id
            )
        ).scalar_one_or_none()
        if not technology_id:
            technology = DetectionTechnology(
                tech=metadata.tech, method_id=metadata.method_id
            )
            self._session.add(technology)
            self._session.flush()
            technology_id = technology.id
        return technology_id

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
        smids = self._session.execute(select(Project.id)).scalars().all()
        smid = gen_short_uuid(SMID_LENGTH, smids)
        contact_id = self._add_contact_if_none(project_template)
        stamp = datetime.now(timezone.utc)  # .isoformat()
        project = Project(
            id=smid,
            title=project_template.title,
            summary=project_template.summary,
            contact_id=contact_id,
            date_published=project_template.date_published,
            date_added=stamp,
        )
        sources = []
        for source in project_template.external_sources:
            source = ProjectSource(project_id=smid, doi=source.doi, pmid=source.pmid)
            sources.append(source)

        logger.info(f"Adding project_template {smid}...")

        self._session.add(project)
        self._session.add_all(sources)
        self._session.flush()
        return smid

    def _write_project_template(
        self, project_template: ProjectTemplate, smid: str, request_uuid: str
    ) -> None:
        metadata_file = Path(self.DATA_PATH, self.METADATA_PATH, f"{smid}.json")
        with open(metadata_file, "w") as fh:
            fh.write(project_template.model_dump_json(indent=4))
        request_file = Path(
            self.DATA_PATH,
            self.METADATA_PATH,
            self.REQUEST_PATH,
            f"{request_uuid}.json",
        )
        request_file.unlink()


@cache
def get_project_service():
    """Helper function to set up a ProjectService object by injecting its dependencies.

    :returns: Project service instance
    :rtype: ProjectService
    """
    return ProjectService(session=get_session())

from datetime import datetime, timezone
import json
import logging
from functools import cache
from pathlib import Path
from typing import ClassVar, Optional, List, Dict

from sqlalchemy.orm import Session
from sqlalchemy import select, func

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
import scimodom.database.queries as queries
from scimodom.services.annotation import AnnotationService
from scimodom.services.assembly import AssemblyService
from scimodom.services.bedtools import get_bedtools_service
from scimodom.services.modification import get_modification_service
from scimodom.services.permission import get_permission_service
import scimodom.utils.specifications as specs
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)


class DuplicateProjectError(Exception):
    """Exception handling for duplicate projects."""

    pass


class ProjectService:
    """Utility class to create, manage, and
    query a project.

    NOTE: Some class attributes are only defined
    for project creation.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param SMID_LENGTH: Length of Sci-ModoM ID (SMID)
    :type SMID_LENGTH: int
    :param DATA_PATH: Data path
    :type DATA_PATH: str | Path | None
    :param DATA_SUB_PATH: Data sub path
    :type DATA_SUB_PATH: str
    """

    SMID_LENGTH: ClassVar[int] = specs.SMID_LENGTH
    DATA_PATH: ClassVar[str | Path] = Config.DATA_PATH
    DATA_SUB_PATH: ClassVar[str] = "metadata"
    DATA_SUB_PATH_SUB: ClassVar[str] = "project_requests"

    def __init__(self, session: Session) -> None:
        """Initializer method."""
        self._session = session

        self._project: dict
        self._smid: str
        self._assemblies: set[tuple[int, str]] = set()

    def __new__(cls, session: Session):
        """Constructor method."""
        if cls.DATA_PATH is None:
            msg = "Missing environment variable: DATA_PATH. Terminating!"
            raise ValueError(msg)
        elif not Path(cls.DATA_PATH, cls.DATA_SUB_PATH).is_dir():
            msg = f"DATA PATH {Path(cls.DATA_PATH, cls.DATA_SUB_PATH)} not found! Terminating!"
            raise FileNotFoundError(msg)
        elif not Path(cls.DATA_PATH, cls.DATA_SUB_PATH, cls.DATA_SUB_PATH_SUB).is_dir():
            msg = f"DATA PATH {Path(cls.DATA_PATH, cls.DATA_SUB_PATH, cls.DATA_SUB_PATH_SUB)} not found! Terminating!"
            raise FileNotFoundError(msg)
        else:
            return super(ProjectService, cls).__new__(cls)

    @staticmethod
    def create_project_request(project: dict):
        """Project request constructor.

        :param project: Project description (json template)
        :type project: dict
        """
        project_request_path = Path(
            ProjectService.DATA_PATH,
            ProjectService.DATA_SUB_PATH,
            ProjectService.DATA_SUB_PATH_SUB,
        )

        uuid = utils.gen_short_uuid(12, [])
        filen = Path(project_request_path, f"{uuid}.json")

        logger.info(f"Writing project request to {filen}...")

        # reformat project template
        forename = project["forename"]
        surname = project["surname"]
        project["contact_name"] = f"{surname}, {forename}"
        project["date_published"] = project.get("date_published", None)
        project["external_sources"] = project.get("external_sources", None)
        for d in utils.to_list(project["external_sources"]):
            d["doi"] = d["doi"] if d["doi"] != "" else None
            d["pmid"] = d["pmid"] if d["pmid"] != "" else None
        for d in utils.to_list(project["metadata"]):
            d["organism"] = {
                "taxa_id": d["taxa_id"],
                "cto": d["cto"],
                "assembly": d["assembly_name"],
            }
            d["extra"] = {
                "assembly_id": d.get("assembly", None),
                "note": d["note"] if d["note"] != "" else None,
            }
            del d["taxa_id"]
            del d["cto"]
            del d["assembly_name"]
            del d["assembly"]
            del d["note"]
        del project["forename"]
        del project["surname"]

        # hard coded length = 12
        with open(filen, "w") as f:
            json.dump(project, f, indent="\t")
        return uuid

    def create_project(self, project: dict) -> None:
        """Project constructor.

        :param project: Project description (json template)
        :type project: dict
        """
        self._project = project

        try:
            self._validate_keys()
            self._validate_entry()
            self._add_selection()
            self._create_smid()
            self._write_metadata()
            self._session.commit()
        except:
            self._session.rollback()
            raise

    def update_assembly_and_annotation(self) -> None:
        """Eventually download assembly chain files,
        genome annotation, and write annotations to
        disk and to the database."""
        try:
            for assembly in self._assemblies:
                taxid, name = assembly
                logger.info(f"Calling AssemblyService for {name} ({taxid})...")
                AssemblyService.from_new(
                    self._session, name=name, taxa_id=taxid
                )  # commit, unless ...
                logger.info(f"Calling AnnotationService for {taxid}...")
                AnnotationService(
                    session=self._session,
                    bedtools_service=get_bedtools_service(),
                    modification_service=get_modification_service(),
                    taxa_id=taxid,
                ).create_annotation()  # commit, unless ...
        except:
            raise

    def associate_project_to_user(self, user: User, smid: str | None = None):
        """Associate a project to a user.
        When called after project creation, the SMID is
        available (default), else nothing is done, unless
        it is passed as argument.

        :param smid: SMID. There is no check
        on the validity of this value, this must be done
        before calling this function.
        :type smid: str
        """
        if not smid:
            try:
                smid = self._smid
            except AttributeError:
                logger.debug("Undefined SMID. Nothing will be done.")
                return
        permission_service = get_permission_service()
        permission_service.insert_into_user_project_association(user, smid)

    def get_smid(self) -> str:
        """Return newly created SMID, else
        raises a ValueError.

        :returns: SMID
        :rtype: str
        """
        try:
            return self._smid
        except AttributeError:
            msg = "Undefined SMID. This is only defined when creating a project."
            raise AttributeError(msg)

    def get_by_id(self, smid: str) -> Project:
        """Retrieve project by SMID

        :param smid: SMID
        :type smid: str
        """
        return self._session.scalars(select(Project).where(Project.id == smid)).one()

    def get_projects(self, user: Optional[User] = None) -> List[Dict[str, any]]:
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

    def _validate_keys(self) -> None:
        """Validate keys from project description (dictionary)."""

        cols = utils.get_table_columns(
            "Project", remove=["id", "date_added", "contact_id"]
        )
        cols.extend(utils.get_table_columns("ProjectContact", remove=["id"]))
        cols.extend(["external_sources", "metadata"])
        utils.check_keys_exist(self._project.keys(), cols)

        if self._project["external_sources"] is not None:
            cols = utils.get_table_columns("ProjectSource", ["id", "project_id"])
            for d in utils.to_list(self._project["external_sources"]):
                utils.check_keys_exist(d.keys(), cols)

        m_cols = utils.get_table_columns("Modification", remove=["id"])
        m_cols.extend(utils.get_table_columns("DetectionTechnology", remove=["id"]))
        m_cols.append("organism")
        o_cols = utils.get_table_columns("Organism", remove=["id"])
        o_cols.append("assembly")
        for d in utils.to_list(self._project["metadata"]):
            utils.check_keys_exist(d.keys(), m_cols)
            utils.check_keys_exist(d["organism"].keys(), o_cols)

    def _get_prj_src(self):
        """Construct query from project "external_sources" """
        from sqlalchemy import tuple_, and_, or_

        ors = or_(False)
        ands = and_(True)

        if self._project["external_sources"] is not None:
            for s in utils.to_list(self._project["external_sources"]):
                doi = s["doi"]
                pmid = s["pmid"]
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

    def _validate_entry(self) -> None:
        """Validate project using title and sources."""
        query = (
            select(func.distinct(Project.id))
            .join_from(Project, ProjectSource, Project.sources, isouter=True)
            .where(Project.title == self._project["title"])
        )
        query = query.where(self._get_prj_src())
        smid = self._session.execute(query).scalar()
        if smid:
            msg = (
                f"At least one similar record exists with SMID = {smid} and "
                f"title = {self._project['title']}. Aborting transaction!"
            )
            raise DuplicateProjectError(msg)

    def _add_selection(self) -> None:
        """Add new selection."""

        # no upsert, add only if on_conflict_do_nothing?
        for d in utils.to_list(self._project["metadata"]):
            # modification
            rna = d["rna"]
            modomics_id = d["modomics_id"]
            query = queries.query_column_where(
                Modification, "id", filters={"rna": rna, "modomics_id": modomics_id}
            )
            modification_id = self._session.execute(query).scalar_one_or_none()
            if not modification_id:
                modification = Modification(rna=rna, modomics_id=modomics_id)
                self._session.add(modification)
                self._session.flush()
                modification_id = modification.id

            # technology
            tech = d["tech"]
            method_id = d["method_id"]
            query = queries.query_column_where(
                DetectionTechnology,
                "id",
                filters={"tech": tech, "method_id": method_id},
            )
            technology_id = self._session.execute(query).scalar_one_or_none()
            if not technology_id:
                technology = DetectionTechnology(tech=tech, method_id=method_id)
                self._session.add(technology)
                self._session.flush()
                technology_id = technology.id

            # organism
            d_organism = d["organism"]
            cto = d_organism["cto"]
            taxa_id = int(d_organism["taxa_id"])
            self._assemblies.add((taxa_id, d_organism["assembly"]))
            query = queries.query_column_where(
                Organism, "id", filters={"cto": cto, "taxa_id": taxa_id}
            )
            organism_id = self._session.execute(query).scalar_one_or_none()
            if not organism_id:
                organism = Organism(cto=cto, taxa_id=taxa_id)
                self._session.add(organism)
                self._session.flush()
                organism_id = organism.id

            # selection
            query = queries.query_column_where(
                Selection,
                "id",
                filters={
                    "modification_id": modification_id,
                    "technology_id": technology_id,
                    "organism_id": organism_id,
                },
            )
            selection_id = self._session.execute(query).scalar_one_or_none()
            if not selection_id:
                msg = f"Adding selection ID ({modification_id}, {organism_id}, {technology_id})"
                logger.info(msg)

                selection = Selection(
                    modification_id=modification_id,
                    organism_id=organism_id,
                    technology_id=technology_id,
                )
                self._session.add(selection)
                self._session.flush()

    def _add_contact(self):
        """Add new contact."""
        contact_name = self._project["contact_name"]
        contact_institution = self._project["contact_institution"]
        contact_email = self._project["contact_email"]
        query = queries.query_column_where(
            ProjectContact,
            "id",
            filters={
                "contact_name": contact_name,
                "contact_institution": contact_institution,
                "contact_email": contact_email,
            },
        )
        contact_id = self._session.execute(query).scalar_one_or_none()
        if not contact_id:
            contact = ProjectContact(
                contact_name=contact_name,
                contact_institution=contact_institution,
                contact_email=contact_email,
            )
            self._session.add(contact)
            self._session.flush()
            contact_id = contact.id
        return contact_id

    def _create_smid(self) -> None:
        """Add project."""

        query = select(Project.id)
        smids = self._session.execute(query).scalars().all()
        self._smid = utils.gen_short_uuid(self.SMID_LENGTH, smids)

        contact_id = self._add_contact()

        stamp = datetime.now(timezone.utc).replace(microsecond=0)  # .isoformat()
        try:
            date_published = datetime.fromisoformat(self._project["date_published"])
        except TypeError:
            date_published = None

        project = Project(
            id=self._smid,
            title=self._project["title"],
            summary=self._project["summary"],
            contact_id=contact_id,
            date_published=date_published,
            date_added=stamp,
        )

        sources = []
        for s in utils.to_list(self._project["external_sources"]):
            source = ProjectSource(project_id=self._smid, doi=s["doi"], pmid=s["pmid"])
            sources.append(source)

        msg = f"Adding project {self._smid}"
        logger.info(msg)

        self._session.add(project)
        self._session.add_all(sources)
        self._session.flush()

    def _write_metadata(self) -> None:
        """Writes a copy of project metadata."""
        parent = Path(self.DATA_PATH, self.DATA_SUB_PATH)
        with open(Path(parent, f"{self._smid}.json"), "w") as f:
            json.dump(self._project, f, indent="\t")


@cache
def get_project_service():
    """Helper function to set up a ProjectService object by injecting its dependencies.

    :returns: Project service instance
    :rtype: ProjectService
    """
    return ProjectService(session=get_session())

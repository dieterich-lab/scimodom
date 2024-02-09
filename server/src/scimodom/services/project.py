#! /usr/bin/env python3

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import ClassVar

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from scimodom.config import Config
from scimodom.database.models import (
    Project,
    ProjectSource,
    ProjectContact,
    Modification,
    DetectionTechnology,
    Organism,
    Selection,
    Assembly,
)
import scimodom.database.queries as queries
from scimodom.services.annotation import AnnotationService
import scimodom.utils.specifications as specs
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)


class DuplicateProjectError(Exception):
    """Exception handling for duplicate projects."""

    pass


class ProjectService:
    """Utility class to create a project.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param project: Project description (json template)
    :type project: dict
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

    def __init__(self, session: Session, project: dict) -> None:
        """Initializer method."""
        self._session = session
        self._project = project
        self._smid: str
        self._assemblies: set[tuple[int, str]] = set()

    def __new__(cls, session: Session, project: dict):
        """Constructor method."""
        if cls.DATA_PATH is None:
            msg = "Missing environment variable: DATA_PATH. Terminating!"
            raise ValueError(msg)
        elif not Path(cls.DATA_PATH, cls.DATA_SUB_PATH).is_dir():
            msg = f"DATA PATH {Path(cls.DATA_PATH, cls.DATA_SUB_PATH)} not found! Terminating!"
            raise FileNotFoundError(msg)
        else:
            return super(ProjectService, cls).__new__(cls)

    def _validate_keys(self) -> None:
        """Validate keys from project description (dictionary)."""
        from itertools import chain

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
                self._session.commit()
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
                self._session.commit()
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
                self._session.commit()
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
                selection = Selection(
                    modification_id=modification_id,
                    technology_id=technology_id,
                    organism_id=organism_id,
                )
                self._session.add(selection)
                self._session.commit()

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
            self._session.commit()
            contact_id = contact.id
        return contact_id

    def _create_smid(self) -> None:
        """Add project."""

        query = select(Project.id)
        smids = self._session.execute(query).scalars().all()
        self._smid = utils.gen_short_uuid(self.SMID_LENGTH, smids)

        contact_id = self._add_contact()

        stamp = datetime.now(timezone.utc).replace(microsecond=0)  # .isoformat()

        project = Project(
            id=self._smid,
            title=self._project["title"],
            summary=self._project["summary"],
            contact_id=contact_id,
            date_published=datetime.fromisoformat(self._project["date_published"]),
            date_added=stamp,
        )

        sources = []
        for s in utils.to_list(self._project["external_sources"]):
            source = ProjectSource(project_id=self._smid, doi=s["doi"], pmid=s["pmid"])
            sources.append(source)

        self._session.add(project)
        self._session.add_all(sources)
        self._session.commit()

    def _write_metadata(self) -> None:
        """Writes a copy of project metadata."""
        parent = Path(self.DATA_PATH, self.DATA_SUB_PATH)
        with open(Path(parent, f"{self._smid}.json"), "w") as f:
            json.dump(self._project, f, indent="\t")

    def create_project(self, wo_assembly: bool = False) -> None:
        """Project constructor."""
        self._validate_keys()
        self._validate_entry()
        self._add_selection()
        self._create_smid()
        self._write_metadata()

        if not wo_assembly:
            pass
            # instantiate AssemblyService
            # one per species/assembly

            # TODO
            # msg = "Preparing annotation for selected organisms"
            # logger.info(msg)
            # for taxid in self._taxa_ids:
            #     service = AnnotationService.from_taxid(self._session, taxid=taxid)

    def get_smid(self) -> str:
        return self._smid

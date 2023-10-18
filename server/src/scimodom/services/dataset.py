#! /usr/bin/env python3

import logging

import scimodom.utils.utils as utils
import scimodom.utils.specifications as specs
import scimodom.database.queries as queries

from typing import TextIO, ClassVar, Optional, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from scimodom.services.importer import EUFImporter
from scimodom.database.models import (
    Data,
    Dataset,
    Association,
    Selection,
    Modomics,
    Modification,
    DetectionTechnology,
    Organism,
    Assembly,
)

logger = logging.getLogger(__name__)


class DuplicateDatasetError(Exception):
    """Exception handling for duplicate dataset."""

    pass


class DataService:
    """Utility class to create a dataset.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param smid: SMID
    :type smid: str
    :param title: Title associated with EUF/bedRMod file/dataset
    :type title: str
    :param filen: EUF/bedRMod file path/name
    :type filen: str
    :param handle: EUF/bedRMod file handle
    :type handle: TextIO
    :param taxa_id: Taxonomy ID (organism) for file/dataset
    :type taxa_id: int
    :param assembly_id: Assembly ID for file/dataset (given at upload, not from file header)
    :type assembly_id: int
    :param modification_ids: Modification(s) associated with file/dataset (from upload)
    :type modification_ids: list[int]
    :param technology_id: Technology ID associated with file/dataset (from upload)
    :type technology_id: int
    :param organism_id: Organism ID associated with file/dataset (from upload)
    :type organism_id: int
    :param EUFID_LENGTH: Length of dataset ID (EUFID)
    :type EUFID_LENGTH: int
    """

    EUFID_LENGTH: ClassVar[int] = specs.EUFID_LENGTH

    def __init__(
        self,
        session: Session,
        smid: str,
        title: str,
        filen: str,
        handle: TextIO,
        taxa_id: int,
        assembly_id: int,
        modification_ids: list[int],
        technology_id: int,
        organism_id: int,
    ) -> None:
        self._eufid: Optional[str] = None
        self._selection_ids: dict = dict()
        self._lifted: bool = False

        self._session = session
        self._smid = smid
        self._title = title
        # how are these coming from form?
        self._filen = filen  # ?
        self._handle = handle
        # maybe these 2 are given as names, and not ids, we just have to query the DB then
        self._taxa_id = taxa_id
        self._assembly_id = assembly_id

        self._modification_ids = modification_ids  # list - selection from FE upload form - eventually check with file content?
        self._technology_id = technology_id  # for now just one
        self._organism_id = organism_id  # for now just one

    def _get_selection(self) -> None:
        """Get selection IDs associated with dataset.

        Note: A selection is made up of modification_id, technology_id, and organism_id.
        """
        for modification_id in self._modification_ids:
            query = queries.query_column_where(
                Selection,
                "id",
                filters={
                    "modification_id": modification_id,
                    "technology_id": self._technology_id,
                    "organism_id": self._organism_id,
                },
            )
            selection_id = self._session.execute(query).scalar()
            query = (
                select(
                    Modomics.short_name,
                    Modification.rna,
                    DetectionTechnology.tech,
                    Organism.cto,
                )
                .join_from(
                    Selection,
                    Modification,
                    Selection.modification_id == Modification.id,
                )
                .join_from(
                    Selection,
                    DetectionTechnology,
                    Selection.technology_id == DetectionTechnology.id,
                )
                .join_from(Selection, Organism, Selection.organism_id == Organism.id)
                .join_from(
                    Modification, Modomics, Modification.modomics_id == Modomics.id
                )
                .where(Selection.id == selection_id)
            )
            try:
                selection = self._session.execute(query).one()
            except:
                query = queries.query_column_where(
                    "Organism", "cto", filters={"id": self._organism_id}
                )
                organism = self._session.execute(query).scalar()
                query = queries.query_column_where(
                    "DetectionTechnology", "tech", filters={"id": self._technology_id}
                )
                technology = self._session.execute(query).scalar()
                query = queries.query_column_where(
                    "Modification", "modomics_id", filters={"id": modification_id}
                )
                modomics_id = self._session.execute(query).scalar()
                query = queries.query_column_where(
                    "Modification", "rna", filters={"id": modification_id}
                )
                rna = self._session.execute(query).scalar()
                query = queries.query_column_where(
                    "Modomics", "short_name", filters={"id": modomics_id}
                )
                short_name = self._session.execute(query).scalar()
                msg = (
                    f"Selection for {short_name} ({rna}), {technology}, "
                    f"and {organism} not found! This is likely due to database corruption or a bug."
                )
                raise Exception(msg)
            self._selection_ids[selection_id] = selection

    def _validate_entry(self) -> None:
        """Validate new dataset using SMID, title, assembly, and selection."""
        for selection_id, selection in self._selection_ids.items():
            query = (
                select(func.distinct(Dataset.id))
                .outerjoin(Association, Dataset.id == Association.dataset_id)
                .where(
                    Association.selection_id == selection_id,
                    Dataset.project_id == self._smid,
                    Dataset.title == self._title,
                    Dataset.assembly_id == self._assembly_id,
                )
            )
            eufid = self._session.execute(query).scalar()  # most likely none or one?
            if eufid:
                msg = (
                    f"A similar record with EUFID = {eufid} already exists for project {self._smid} "
                    f"with title = {self._title}, and the following selection: {selection[0]}, "
                    f"{selection[1]}, and {selection[2]}. Aborting transaction!"
                )
                raise DuplicateDatasetError(msg)

    def _validate_assembly(self) -> None:
        """Validate assembly and mark dataset for liftover"""
        query = queries.get_assembly_version()
        db_assembly_version = self._session.execute(query).scalar()

        query = queries.query_column_where(
            "Assembly", "version", filters={"id": self._assembly_id}
        )
        assembly_version = self._session.execute(query).scalar()

        if not assembly_version == db_assembly_version:
            self._lifted = True
            print("Some message... do something when?")

    def _create_eufid(self) -> None:
        """Create new dataset using EUFimporter class."""
        query = select(Dataset.id)
        eufids = self._session.execute(query).scalars().all()
        self._eufid = utils.gen_short_uuid(self.EUFID_LENGTH, eufids)

        importer = EUFImporter(
            self._session,
            self._filen,
            self._handle,
            self._smid,
            self._eufid,
            self._title,
            self._taxa_id,
            self._assembly_id,
            self._lifted,
        )
        importer.parseEUF()

        modifications = {s[0] for s in self._selection_ids.values()}
        modifications = {m.lower() for m in modifications}
        modifications_from_file = importer.get_modifications_from_file()
        modifications_from_file = {m.lower() for m in modifications_from_file}
        symdiff = modifications.symmetric_difference(modifications_from_file)
        if symdiff:
            msg = (
                f"Selection for modification and modifications read from {self._filen} "
                f"differ: {symdiff}. Aborting transaction!"
            )
            raise Exception(msg)

        selection_str = " and ".join(
            [", ".join(map(str, s)) for s in self._selection_ids.values()]
        )
        msg = (
            f"Adding dataset {self._eufid} to project {self._smid} with title = {self._title}, "
            f"and the following selection: {selection_str}."
        )
        logger.info(msg)
        # confirm ?
        importer.close()

    def _add_association(self) -> None:
        """Create new association entry for dataset.

        Note: An association is made up of dataset_id and selection_id
        """
        for selection_id in self._selection_ids.keys():
            association = Association(dataset_id=self._eufid, selection_id=selection_id)
            self._session.add(association)
            self._session.commit()

    def create_dataset(self) -> None:
        """Dataset constructor."""
        self._get_selection()
        self._validate_entry()
        self._validate_assembly()

        self._create_eufid()
        self._add_association()

        # if self._lifted, upsert table records for this newly added dataset with "lifted" data...
        # what for annotations?

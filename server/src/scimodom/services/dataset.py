import logging
from pathlib import Path
from typing import ClassVar, Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from scimodom.database.models import (
    # Data,
    Dataset,
    Association,
    Selection,
    Modomics,
    Modification,
    DetectionTechnology,
    Organism,
    # Assembly,
)
import scimodom.database.queries as queries

# from scimodom.services.importer import EUFImporter
import scimodom.utils.specifications as specs
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)


class InstantiationError(Exception):
    """Exception handling for DataService instantiation."""

    pass


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
    :param filen: EUF/bedRMod file path
    :type filen: str | Path
    :param assembly_id: Assembly ID. This is not the
    assembly name from a EU formatted file header.
    :type assembly_id: int
    :param selection_id: Selection ID(s) associated with dataset
    :type selection_id: int or list of int
    :param modification_id: Modification ID(s) associated with dataset
    :type modification_id: int or list of int
    :param technology_id: Technology ID associated with dataset
    :type technology_id: int
    :param organism_id: Organism ID associated with dataset
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
        filen: str | Path,
        assembly_id: int,
        **kwargs,
    ) -> None:
        """Initializer method."""
        self._session = session
        self._smid = smid
        self._title = title
        self._filen = filen
        self._assembly_id = assembly_id

        self._selection_id: list[int]
        self._modification_id: list[int]
        self._technology_id: int
        self._organism_id: int
        self._association: dict[str, int]
        self._eufid: str

        selection_id = kwargs.get("selection_id", None)
        if selection_id is not None:
            query = select(Selection.id)
            ids = session.execute(query).scalars().all()
            for sid in selection_id:
                if sid not in ids:
                    msg = f"Selection ID = {sid} not found! Aborting transaction!"
                    raise ValueError(msg)
            self._selection_id = selection_id
            self._set_ids()
        else:
            modification_id = kwargs.get("modification_id", None)
            query = select(Modification.id)
            ids = session.execute(query).scalars().all()
            for mid in modification_id:
                if mid not in ids:
                    msg = f"Modification ID = {mid} not found! Aborting transaction!"
                    raise ValueError(msg)
            self._modification_id = modification_id
            technology_id = kwargs.get("technology_id", None)
            query = select(DetectionTechnology.id)
            ids = session.execute(query).scalars().all()
            if technology_id not in ids:
                msg = f"Modification ID = {technology_id} not found! Aborting transaction!"
                raise ValueError(msg)
            self._technology_id = technology_id
            organism_id = kwargs.get("organism_id", None)
            query = select(Organism.id)
            ids = session.execute(query).scalars().all()
            if organism_id not in ids:
                msg = f"Organism ID = {organism_id} not found! Aborting transaction!"
                raise ValueError(msg)
            self._organism_id = organism_id
            self._set_selection()

    @classmethod
    def from_selection(
        cls,
        session: Session,
        smid: str,
        title: str,
        filen: str | Path,
        assembly_id: int,
        selection_id: int | list[int],
    ):
        """Provides DataService factory when selection ID
        is known.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param smid: SMID
        :type smid: str
        :param title: Title associated with EUF/bedRMod file/dataset
        :type title: str
        :param filen: EUF/bedRMod file path
        :type filen: str | Path
        :param assembly_id: Assembly ID. This is not the
        assembly name from a EU formatted file header.
        :type assembly_id: int
        :param selection_id: Selection ID(s)
        :type selection_id: int or list of int
        :returns: DataService class instance
        :rtype: DataService
        """
        ids = utils.to_list(selection_id)
        if len(set(ids)) != len(ids):
            msg = "Repeated selection IDs. Cannot instantiate DataService!"
            raise InstantiationError(msg)
        service = cls(session, smid, title, filen, assembly_id, selection_id=ids)
        return service

    @classmethod
    def from_new(
        cls,
        session: Session,
        smid: str,
        title: str,
        filen: str | Path,
        assembly_id: int,
        modification_id: int | list[int],
        technology_id: int,
        organism_id: int,
    ):
        """Provides DataService factory to instantiate class with
        modification_id, technology_id, and organism_id, which
        make up a unique selection.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param smid: SMID
        :type smid: str
        :param title: Title associated with EUF/bedRMod file/dataset
        :type title: str
        :param filen: EUF/bedRMod file path
        :type filen: str | Path
        :param assembly_id: Assembly ID. This is not the
        assembly name from a EU formatted file header.
        :type assembly_id: int
        :param modification_id: Modification ID(s) (RNA type, modomics ID)
        :type modification_id: int or list of int
        :param technology_id: Technology ID (method ID, technology)
        :type technology_id: int
        :param organism_id: Organism ID (taxa ID, cto)
        :type organism_id: int
        :returns: DataService class instance
        :rtype: DataService
        """
        ids = utils.to_list(modification_id)
        if len(set(ids)) != len(ids):
            msg = "Repeated modification IDs. Cannot instantiate DataService!"
            raise InstantiationError(msg)
        service = cls(
            session,
            smid,
            title,
            filen,
            assembly_id,
            modification_id=ids,
            technology_id=technology_id,
            organism_id=organism_id,
        )
        return service

    def _set_ids(self) -> None:
        """Set modification_id, technology_id,
        and organism_id from selection_id."""
        modification_id = []
        technology_id = None
        organism_id = None
        for selection_id in self._selection_id:
            query = (
                select(
                    Modification.id,
                    Modomics.short_name,
                    DetectionTechnology.id,
                    Organism.id,
                )
                .join_from(
                    Selection,
                    Modification,
                    Selection.inst_modification,
                )
                .join_from(
                    Selection,
                    DetectionTechnology,
                    Selection.inst_technology,
                )
                .join_from(Selection, Organism, Selection.inst_organism)
                .join_from(Modification, Modomics, Modification.inst_modomics)
                .where(Selection.id == selection_id)
            )
            selection = self._session.execute(query).one()
            modification_id.append(selection[0])
            if technology_id is None:
                technology_id = selection[2]
            if technology_id != selection[2]:
                msg = (
                    f"Two different technology IDs {technology_id} and "
                    f"{selection[2]} are associated with this dataset. "
                    "Aborting transaction!"
                )
                raise InstantiationError(msg)
            if organism_id is None:
                organism_id = selection[3]
            if organism_id != selection[3]:
                msg = (
                    f"Two different organism IDs {organism_id} and "
                    f"{selection[3]} are associated with this dataset. "
                    "Aborting transaction!"
                )
                raise InstantiationError(msg)
            self._association[selection[1]] = selection_id
        if len(set(modification_id)) != len(modification_id):
            msg = (
                f"Repeated modification IDs {','.join([i for i in modification_id])} are "
                "associated with this dataset. Aborting transaction!"
            )
            raise InstantiationError(msg)
        self._modification_id = modification_id
        self._technology_id = technology_id
        self._organism_id = organism_id

    def _set_selection(self) -> None:
        """Set selection IDs associated with dataset."""
        selection_id = []
        for modification_id in self._modification_id:
            query = queries.query_column_where(
                Selection,
                "id",
                filters={
                    "modification_id": modification_id,
                    "technology_id": self._technology_id,
                    "organism_id": self._organism_id,
                },
            )
            selection_id.append(self._session.execute(query).scalar_one())
            query = (
                select(
                    Modomics.short_name,
                )
                .join_from(Modification, Modomics, Modification.inst_modomics)
                .where(Modification.id == modification_id)
            )
            name = self._session.execute(query).one()
            self._association[name] = selection_id[-1]
        if len(set(selection_id)) != len(selection_id):
            msg = (
                f"Repeated selection IDs {','.join([i for i in selection_id])} are "
                "associated with this dataset. Aborting transaction!"
            )
            raise InstantiationError(msg)
        self._selection_id = selection_id

    def _validate_entry(self) -> None:
        """Validate new dataset using SMID, title, assembly, and selection."""
        pass
        # for selection_id, selection in self._selection_ids.items():
        #     query = (
        #         select(func.distinct(Dataset.id)).join_from(
        #             Dataset, Association, Dataset.associations, isouter=True
        #         )
        #         # .outerjoin(Association, Dataset.id == Association.dataset_id)
        #         .where(
        #             Association.selection_id == selection_id,
        #             Dataset.project_id == self._smid,
        #             Dataset.title == self._title,
        #             # TODO
        #             # Dataset.assembly_id == self._assembly_id,
        #         )
        #     )
        #     eufid = self._session.execute(query).scalar()  # most likely none or one?
        #     if eufid:
        #         msg = (
        #             f"A similar record with EUFID = {eufid} already exists for project {self._smid} "
        #             f"with title = {self._title}, and the following selection: {selection[0]}, "
        #             f"{selection[1]}, and {selection[2]}. Aborting transaction!"
        #         )
        #         raise DuplicateDatasetError(msg)

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

    def _add_association(self) -> None:
        """Create new association entry for dataset.

        Note: An association is made up of dataset_id and selection_id
        """
        pass
        # for selection_id in self._selection_ids.keys():
        #     association = Association(dataset_id=self._eufid, selection_id=selection_id)
        #     self._session.add(association)
        #     self._session.flush()

    def _create_eufid(self) -> None:
        """Create new dataset using EUFimporter class."""
        pass
        # try:
        #     query = select(Dataset.id)
        #     eufids = self._session.execute(query).scalars().all()
        #     self._eufid = utils.gen_short_uuid(self.EUFID_LENGTH, eufids)

        #     self._add_association()

        #     importer = EUFImporter(
        #         self._session,
        #         self._filen,
        #         self._handle,
        #         self._smid,
        #         self._eufid,
        #         self._title,
        #         self._taxa_id,
        #         self._assembly_id,
        #         self._lifted,
        #         # TODO assume modification is unique for any combination of RNA, tech, and cto...
        #         # i.e. a dataset can have 1+ modification, but only 1 RNA type, 1 technology, and 1 cto
        #         # so we cannot have e.g. twice m6A
        #         {k: v[0] for k, v in self._selection_ids.items()},
        #         data_path=self._data_path,
        #     )
        #     importer.parseEUF()

        #     # TODO
        #     # modifications = {s[0] for s in self._selection_ids.values()}
        #     # modifications = {m.lower() for m in modifications}
        #     # modifications_from_file = importer.get_modifications_from_file()
        #     # modifications_from_file = {m.lower() for m in modifications_from_file}
        #     # symdiff = modifications.symmetric_difference(modifications_from_file)
        #     # if symdiff:
        #     #     msg = (
        #     #         f"Selection for modification and modifications read from {self._filen} "
        #     #         f"differ: {symdiff}. Aborting transaction!"
        #     #     )
        #     #     raise Exception(msg)

        #     selection_str = " and ".join(
        #         [", ".join(map(str, s)) for s in self._selection_ids.values()]
        #     )
        #     msg = (
        #         f"Adding dataset {self._eufid} to project {self._smid} with title = {self._title}, "
        #         f"and the following selection: {selection_str}."
        #     )
        #     logger.info(msg)
        # except:
        #     self._session.rollback()
        #     raise
        # else:
        #     # confirm ?
        #     importer.close()

    def create_dataset(self) -> str:
        """Dataset constructor.

        :returns: EUFID
        :rtype: str
        """
        self._get_selection()
        self._validate_entry()
        self._validate_assembly()

        self._create_eufid()

        return self._eufid

        # if self._lifted, upsert table records for this newly added dataset with "lifted" data...
        # what for annotations?

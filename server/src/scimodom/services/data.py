import logging
from pathlib import Path
from typing import ClassVar, Any

from sqlalchemy import select, exists, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

import scimodom.database.queries as queries
import scimodom.utils.specifications as specs
import scimodom.utils.utils as utils
from scimodom.database.models import (
    Assembly,
    Association,
    Dataset,
    DetectionTechnology,
    Modomics,
    Modification,
    Organism,
    Project,
    Selection,
    Taxa,
)
from scimodom.services.annotation import AnnotationService
from scimodom.services.assembly import AssemblyService, AssemblyVersionError
from scimodom.services.importer import get_importer

logger = logging.getLogger(__name__)


class InstantiationError(Exception):
    """Exception handling for DataService instantiation."""

    pass


class SelectionExistsError(Exception):
    """Exception handling for Dataset instantiation
    (from new) with a choice of modification, organism,
    and technology that does not exists."""

    pass


class DatasetExistsError(Exception):
    """Exception for handling Dataset instantiation,
    e.g. suspected duplicate entries."""

    pass


class DatasetHeaderError(Exception):
    """Exception for handling mismatch between
    dataset header and input values."""

    pass


class DataService:
    """Utility class to create a dataset, and import
    data records.

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
    :param selection_ids: Selection ID(s) associated with dataset
    :type selection_ids: int or list of int
    :param modification_ids: Modification ID(s) associated with dataset
    :type modification_ids: int or list of int
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

        self._association: dict[str, int] = dict()

        self._selection_ids: list[int]
        self._modification_ids: list[int]
        self._organism_id: int
        self._technology_id: int
        self._eufid: str

        selection_ids = kwargs.get("selection_ids", None)
        if selection_ids is not None:
            self._selection_ids = selection_ids
        else:
            self._modification_ids = kwargs["modification_ids"]
            self._organism_id = kwargs["organism_id"]
            self._technology_id = kwargs["technology_id"]

    @classmethod
    def from_selection(
        cls,
        session: Session,
        smid: str,
        title: str,
        filen: str | Path,
        assembly_id: int,
        selection_ids: int | list[int],
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
        :param selection_ids: Selection ID(s)
        :type selection_ids: int or list of int
        :returns: DataService class instance
        :rtype: DataService
        """
        is_found = session.query(exists().where(Project.id == smid)).scalar()
        if not is_found:
            msg = f"Unrecognised SMID {smid}. Cannot instantiate DataService!"
            raise InstantiationError(msg)
        sids = utils.to_list(selection_ids)
        if len(set(sids)) != len(sids):
            msg = "Repeated selection IDs. Cannot instantiate DataService!"
            raise InstantiationError(msg)
        for sid in sids:
            is_found = session.query(exists().where(Selection.id == sid)).scalar()
            if not is_found:
                msg = f"Selection ID = {sid} not found! Cannot instantiate DataService!"
                raise InstantiationError(msg)
        service = cls(session, smid, title, filen, assembly_id, selection_ids=sids)
        # retrieve modification, organism, and technology IDs from selection IDs
        service._set_ids()
        return service

    @classmethod
    def from_options(
        cls,
        session: Session,
        smid: str,
        title: str,
        filen: str | Path,
        assembly_id: int,
        modification_ids: int | list[int],
        technology_id: int,
        organism_id: int,
    ):
        """Provides DataService factory to instantiate class with
        selected options: modification_id, technology_id, and
        organism_id, which make up a unique selection.

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
        :param modification_ids: Modification ID(s) (RNA type, modomics ID)
        :type modification_ids: int or list of int
        :param technology_id: Technology ID (method ID, technology)
        :type technology_id: int
        :param organism_id: Organism ID (taxa ID, cto)
        :type organism_id: int
        :returns: DataService class instance
        :rtype: DataService
        """
        is_found = session.query(exists().where(Project.id == smid)).scalar()
        if not is_found:
            msg = f"Unrecognised SMID {smid}. Cannot instantiate DataService!"
            raise InstantiationError(msg)
        mids = utils.to_list(modification_ids)
        if len(set(mids)) != len(mids):
            msg = "Repeated modification IDs. Cannot instantiate DataService!"
            raise InstantiationError(msg)
        # actually instantiate, then validate...
        service = cls(
            session,
            smid,
            title,
            filen,
            assembly_id,
            modification_ids=mids,
            technology_id=technology_id,
            organism_id=organism_id,
        )
        for mid in mids:
            try:
                _ = service._modification_id_to_name(mid)
            except NoResultFound:
                msg = f"Modification ID = {mid} not found! Cannot instantiate DataService!"
                raise InstantiationError(msg)
        try:
            _ = service._technology_id_to_tech(technology_id)
        except NoResultFound:
            msg = f"Technology ID = {technology_id} not found! Cannot instantiate DataService!"
            raise InstantiationError(msg)
        try:
            _ = service._organism_id_to_organism(organism_id)
        except NoResultFound:
            msg = f"Organism ID = {organism_id} not found! Cannot instantiate DataService!"
            raise InstantiationError(msg)
        # retrieve selection ID from selected options
        service._set_selection()
        return service

    @staticmethod
    def validate_imported(name: str, form_value: Any, header_value: Any) -> None:
        """Compare a given input value to the
        matching value read from a file.

        :param name: Parameter name
        :type name: str
        :param form_value: Input parameter value
        :type form_value: Any
        :param header_value: Parameter value
        read from the file header
        :type header_value: Any
        """
        if not form_value == header_value:
            msg = (
                f"Expected {form_value} for {name}; got {header_value} (file header). "
                f"Aborting transaction!"
            )
            raise DatasetHeaderError(msg)

    def create_dataset(self) -> None:
        """Dataset constructor."""
        is_liftover: bool = False

        logger.info("Creating dataset...")

        # test for duplicate dataset
        self._validate_entry()

        # instantiate AssemblyService
        (
            assembly_name,
            current_assembly_name,
            taxa_id,
            organism_name,
        ) = self._query_missing_from_assembly()
        try:
            assembly_service = AssemblyService.from_id(
                self._session, assembly_id=self._assembly_id
            )
        except AssemblyVersionError:
            assembly_service = AssemblyService.from_new(
                self._session, name=assembly_name, taxa_id=taxa_id
            )
            if assembly_service._assembly_id != self._assembly_id:
                msg = (
                    f"Mismatch in assembly versions: {self._assembly_id} and "
                    f"{assembly_service._assembly_id}. Aborting transaction!"
                )
                raise AssemblyVersionError(msg)
            is_liftover = True
        finally:
            seqids = assembly_service.get_seqids(organism_name, current_assembly_name)

        # create EUFID
        self._create_eufid()

        # import
        checkpoint = self._session.begin_nested()
        try:
            try:
                filen = self._filen.as_posix()  # type: ignore
            except:
                filen = self._filen
            importer = get_importer(
                filen=filen,
                smid=self._smid,
                eufid=self._eufid,
                title=self._title,
            )
            importer.header.parse_header()
            # compare input and header
            self.validate_imported("organism", taxa_id, importer.header.taxid)
            self.validate_imported("assembly", assembly_name, importer.header.assembly)
            importer.header.close()  # flush
            # add association = (EUFID, selection)
            # update self._association dict
            self._add_association()  # flush
            # instantiate data importer
            importer.init_data_importer(
                association=self._association, seqids=seqids, no_flush=is_liftover
            )
            importer.data.parse_records()
            importer.data.close(raise_missing=True)  # flush
        except:
            checkpoint.rollback()
            raise
        else:
            if is_liftover:
                msg = f"Lifting over dataset from {assembly_name} to {current_assembly_name}..."
                logger.info(msg)

                records = importer.data.get_buffer()
                # https://github.com/dieterich-lab/scimodom/issues/76
                # overwrite name with association, remove asociation, add association back after liftover
                records = [
                    {**record, "name": self._association[record["name"]]}
                    for record in records
                ]
                records = [
                    tuple(
                        [val for key, val in record.items() if key != "association_id"]
                    )
                    for record in records
                ]
                try:
                    lifted_file = assembly_service.liftover(records)
                    importer.reset_data_importer(lifted_file)
                    importer.data.parse_records()
                    importer.data.close()  # flush
                except:
                    checkpoint.rollback()
                    raise

        logger.info("Annotating data now...")

        # annotate newly imported data...
        annotation_service = AnnotationService(session=self._session, taxa_id=taxa_id)
        try:
            annotation_service.annotate_data(self._eufid)
            self._session.commit()
        except:
            checkpoint.rollback()
            raise
        # ... update cache
        annotation_service.update_gene_cache(self._selection_ids)

        msg = (
            f"Added dataset {self._eufid} to project {self._smid} with title = {self._title}, "
            f"and the following associations: {', '.join([f'{k}:{v}' for k, v in self._association.items()])}. "
        )
        logger.info(msg)

    def get_eufid(self) -> str:
        """Return newly created EUFID.

        :returns: EUFID
        :rtype: str
        """
        return self._eufid

    def _set_ids(self) -> None:
        """Set modification_id, technology_id,
        and organism_id from selection_id.

        A dataset can be associated with more
        than one selection_id, but organism_id
        and technology_id must be identical."""
        modification_ids: list = []
        technology_id: int
        organism_id: int
        for selection_id in self._selection_ids:
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
            modification_ids.append(selection[0])
            try:
                technology_id  # noqa: F821
            except:
                technology_id = selection[2]
            if technology_id != selection[2]:
                tech1 = self._technology_id_to_tech(technology_id)
                tech2 = self._technology_id_to_tech(selection[2])
                msg = (
                    f"Different technologies {tech1} and {tech2} "
                    "cannot be associated with the same dataset. "
                    "Cannot instantiate DataService!"
                )
                raise InstantiationError(msg)
            try:
                organism_id  # noqa: F821
            except:
                organism_id = selection[3]
            if organism_id != selection[3]:
                cto1, org_name1 = self._organism_id_to_organism(organism_id)
                cto2, org_name2 = self._organism_id_to_organism(selection[3])
                msg = (
                    f"Different organisms {org_name1} ({cto1}) and "
                    f"{org_name2} ({cto2}) cannot be associated with the "
                    "same dataset. Cannot instantiate DataService!"
                )
                raise InstantiationError(msg)
            self._association[selection[1]] = selection_id
        # this cannot actually happen...
        if len(set(modification_ids)) != len(modification_ids):
            m_names = [self._modification_id_to_name(mid) for mid in modification_ids]
            msg = (
                f"Repeated modifications {','.join([m for m in m_names])} "
                "cannot be associated with the same dataset. Cannot instantiate DataService!"
            )
            raise InstantiationError(msg)
        self._modification_ids = modification_ids
        self._technology_id = technology_id
        self._organism_id = organism_id

    def _set_selection(self) -> None:
        """Set selection IDs associated with a
        dataset. Depending on the choice of
        modification_id(s), organism_id, and
        technology_id, a selection_id may or may
        not exists. If it does not exists, a
        SelectionExistsError is raised."""
        selection_ids = []
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
            try:
                selection_ids.append(self._session.execute(query).scalar_one())
            except NoResultFound as exc:
                m_name = self._modification_id_to_name(modification_id)
                tech = self._technology_id_to_tech(self._technology_id)
                cto, org_name = self._organism_id_to_organism(self._organism_id)
                msg = (
                    f"Selection (mod={m_name}, tech={tech}, "
                    f"organism=({org_name}, {cto})) does not exists. "
                    "Aborting transaction!"
                )
                raise SelectionExistsError(msg) from exc
            name = self._modification_id_to_name(modification_id)
            self._association[name] = selection_ids[-1]
        # this cannot actually happen...
        if len(set(selection_ids)) != len(selection_ids):
            msg = (
                f"Repeated selection IDs {','.join([i for i in selection_ids])} are "
                "associated with this dataset. Cannot instantiate DataService!"
            )
            raise InstantiationError(msg)
        self._selection_ids = selection_ids

    def _validate_entry(self) -> None:
        """Tentatively check if dataset already exists using
        SMID, title, and selection.

        Raises DatasetExistsError
        """
        for selection_id in self._selection_ids:
            query = (
                select(func.distinct(Dataset.id))
                .join_from(Dataset, Association, Dataset.associations, isouter=True)
                .where(
                    Association.selection_id == selection_id,
                    Dataset.project_id == self._smid,
                    Dataset.title == self._title,
                )
            )
            eufid = self._session.execute(query).scalar_one_or_none()
            if eufid:
                msg = (
                    f"Suspected duplicate record with EUFID = {eufid} (SMID = {self._smid}), "
                    f'title = "{self._title}", and selection ID = {selection_id}. '
                    f"Aborting transaction!"
                )
                raise DatasetExistsError(msg)

    def _add_association(self) -> None:
        """Create new association entry for dataset."""
        for name, selection_id in self._association.items():
            association = Association(dataset_id=self._eufid, selection_id=selection_id)
            self._session.add(association)
            self._session.flush()
            # update dict
            self._association[name] = association.id

    def _create_eufid(self) -> None:
        """Create new dataset ID."""
        query = select(Dataset.id)
        eufids = self._session.execute(query).scalars().all()
        self._eufid = utils.gen_short_uuid(self.EUFID_LENGTH, eufids)

    def _modification_id_to_name(self, idx: int) -> str:
        """Retrieve modification name for id.

        :param idx: id (PK)
        :type idx: int
        """
        query = (
            select(Modomics.short_name)
            .join(Modification, Modomics.modifications)
            .where(Modification.id == idx)
        )
        return self._session.execute(query).scalar_one()

    def _organism_id_to_organism(self, idx: int) -> str:
        """Retrieve cto and organism name for id.

        :param idx: id (PK)
        :type idx: int
        """
        query = (
            select(Organism.cto, Taxa.short_name)
            .join(Taxa, Organism.inst_taxa)
            .where(Organism.id == idx)
        )
        return self._session.execute(query).one()

    def _technology_id_to_tech(self, idx: int) -> str:
        """Retrieve technology name for id.

        :param idx: id (PK)
        :type idx: int
        """
        query = select(DetectionTechnology.tech).where(DetectionTechnology.id == idx)
        return self._session.execute(query).scalar_one()

    def _query_missing_from_assembly(self) -> tuple[str, str, int, str]:
        """Retrieve assembly-related information.

        :returns: assembly name for instance and database, taxa ID and
        organism name
        :rtype: tuuple of (str, str, int, str)
        """
        query = queries.query_column_where(
            Assembly, ["name", "taxa_id"], filters={"id": self._assembly_id}
        )
        assembly_name, taxa_id = self._session.execute(query).one()
        query = queries.query_column_where(Taxa, "name", filters={"id": taxa_id})
        organism_name = self._session.execute(query).scalar_one()

        query = queries.get_assembly_version()
        version = self._session.execute(query).scalar_one()
        query = queries.query_column_where(
            Assembly, "name", filters={"taxa_id": taxa_id, "version": version}
        )
        current_assembly_name = self._session.execute(query).scalar_one()
        return assembly_name, current_assembly_name, taxa_id, organism_name

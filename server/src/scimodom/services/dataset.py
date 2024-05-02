import logging
from pathlib import Path
from typing import ClassVar, Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

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
import scimodom.database.queries as queries
from scimodom.services.annotation import AnnotationService
from scimodom.services.assembly import AssemblyService, AssemblyVersionError
from scimodom.services.importer import get_importer, get_bed_importer
import scimodom.utils.specifications as specs
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)


class InstantiationError(Exception):
    """Exception handling for DataService instantiation."""

    pass


class DatasetError(Exception):
    """Exception for handling Dataset instantiation,
    e.g. suspected duplicate entries."""

    pass


class DatasetHeaderError(Exception):
    """Exception for handling mismatch between
    dataset header and input values."""

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

        self._association: dict[str, int] = dict()

        self._selection_id: list[int]
        self._modification_id: list[int]
        self._technology_id: int
        self._organism_id: int
        self._eufid: str

        selection_id = kwargs.get("selection_id", None)
        if selection_id is not None:
            query = select(Selection.id)
            ids = self._session.execute(query).scalars().all()
            for sid in selection_id:
                if sid not in ids:
                    msg = f"Selection ID = {sid} not found! Aborting transaction!"
                    raise ValueError(msg)
            self._selection_id = selection_id
            self._set_ids()
        else:
            modification_id = kwargs.get("modification_id", None)
            query = select(Modification.id)
            ids = self._session.execute(query).scalars().all()
            for mid in modification_id:
                if mid not in ids:
                    msg = f"Modification ID = {mid} not found! Aborting transaction!"
                    raise ValueError(msg)
            self._modification_id = modification_id
            technology_id = kwargs.get("technology_id", None)
            query = select(DetectionTechnology.id)
            ids = self._session.execute(query).scalars().all()
            if technology_id not in ids:
                msg = (
                    f"Technology ID = {technology_id} not found! Aborting transaction!"
                )
                raise ValueError(msg)
            self._technology_id = technology_id
            organism_id = kwargs.get("organism_id", None)
            query = select(Organism.id)
            ids = self._session.execute(query).scalars().all()
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
        query = select(Project.id)
        smids = session.execute(query).scalars().all()
        if smid not in smids:
            msg = f"Unrecognised SMID {smid}. Cannot instantiate DataService!"
            raise InstantiationError(msg)
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
        query = select(Project.id)
        smids = session.execute(query).scalars().all()
        if smid not in smids:
            msg = f"Unrecognised SMID {smid}. Cannot instantiate DataService!"
            raise InstantiationError(msg)
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

        # make sure we do not already have a dataset with
        # the same combination of SMID, selection, and title
        self._validate_entry()

        # instantiate AssemblyService
        query = queries.query_column_where(
            Assembly, ["name", "taxa_id"], filters={"id": self._assembly_id}
        )
        assembly_name, taxa_id = self._session.execute(query).all()[0]
        query = queries.query_column_where(Taxa, "name", filters={"id": taxa_id})
        organism_name = self._session.execute(query).scalar_one()
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
            query = queries.get_assembly_version()
            version = self._session.execute(query).scalar_one()
            query = queries.query_column_where(
                Assembly, "name", filters={"taxa_id": taxa_id, "version": version}
            )
            current_assembly_name = self._session.execute(query).scalar_one()
            parent, filen = assembly_service.get_chrom_path(
                organism_name, current_assembly_name
            )
            chrom_file = Path(parent, filen)
            with open(chrom_file, "r") as f:
                lines = f.readlines()
            seqids = [l.split()[0] for l in lines]

        # create EUFID
        self._create_eufid()

        # import
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
            # TODO if importer fails, then checkpoint does not exists...
            checkpoint = importer.header.checkpoint
            importer.header.parse_header()
            # compare input vs. values read from file header
            # for organism (taxa ID) and assembly
            self.validate_imported("organism", taxa_id, importer.header.taxid)
            self.validate_imported("assembly", assembly_name, importer.header.assembly)
            importer.header.close()  # commit
            # add association = (EUFID, selection)
            # update self._association dict
            self._add_association()  # flush
            # instantiate data importer
            importer.init_data_importer(
                association=self._association, seqids=seqids, no_flush=is_liftover
            )
            importer.data.parse_records()
        except:
            checkpoint.rollback()
            raise
        else:
            importer.data.close()  # commit unless...
            if is_liftover:
                msg = f"Lifting over dataset from {assembly_name} to {current_assembly_name}..."
                logger.debug(msg)

                # ... data has not been written to database yet
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
                filen = assembly_service.liftover(records)
                importer.reset_data_importer(filen)
                importer.data.parse_records()
                importer.data.close()

        msg = (
            f"Added dataset {self._eufid} to project {self._smid} with title = {self._title}, "
            f"and the following associations: {', '.join([f'{k}:{v}' for k, v in self._association.items()])}. "
            "Annotating data now..."
        )
        logger.debug(msg)

        # annotate newly imported data, update cache
        annotation_service = AnnotationService(session=self._session, taxa_id=taxa_id)
        annotation_service.annotate_data(self._eufid)
        annotation_service.update_gene_cache(self._selection_id)

    def get_eufid(self) -> str:
        """Return newly created EUFID.

        :returns: EUFID
        :rtype: str
        """
        return self._eufid

    def _set_ids(self) -> None:
        """Set modification_id, technology_id,
        and organism_id from selection_id."""
        modification_id: list = []
        technology_id: int
        organism_id: int
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
            try:
                technology_id  # noqa: F821
            except:
                technology_id = selection[2]
            if technology_id != selection[2]:
                msg = (
                    f"Two different technology IDs {technology_id} and "
                    f"{selection[2]} are associated with this dataset. "
                    "Aborting transaction!"
                )
                raise InstantiationError(msg)
            try:
                organism_id  # noqa: F821
            except:
                organism_id = selection[3]
            if organism_id != selection[3]:
                msg = (
                    f"Two different organism IDs {organism_id} and "
                    f"{selection[3]} are associated with this dataset. "
                    "Aborting transaction!"
                )
                raise InstantiationError(msg)
            self._association[selection[1]] = selection_id
        # this cannot actually happen...
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
            try:
                selection_id.append(self._session.execute(query).scalar_one())
            except Exception as exc:
                msg = (
                    f"Selection (mod={modification_id}, tech={self._technology_id}, "
                    f"organism={self._organism_id}) does not exists. Aborting transaction!"
                )
                raise InstantiationError(msg) from exc
            query = (
                select(
                    Modomics.short_name,
                )
                .join_from(Modification, Modomics, Modification.inst_modomics)
                .where(Modification.id == modification_id)
            )
            name = self._session.execute(query).scalar_one()
            self._association[name] = selection_id[-1]
        # this cannot actually happen...
        if len(set(selection_id)) != len(selection_id):
            msg = (
                f"Repeated selection IDs {','.join([i for i in selection_id])} are "
                "associated with this dataset. Aborting transaction!"
            )
            raise InstantiationError(msg)
        self._selection_id = selection_id

    def _validate_entry(self) -> None:
        """Tentatively check if dataset already exists using
        SMID, title, and selection."""
        for selection_id in self._selection_id:
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
                    f"A similar record with EUFID = {eufid} already exists for project {self._smid} "
                    f"with title = {self._title}, and the following selection ID {selection_id}. "
                    f"Aborting transaction!"
                )
                raise DatasetError(msg)

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

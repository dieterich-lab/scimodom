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
    Dataset,
    DatasetModificationAssociation,
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
from scimodom.services.bedtools import get_bedtools_service
from scimodom.services.importer import get_importer
from scimodom.services.modification import get_modification_service

logger = logging.getLogger(__name__)


class InstantiationError(Exception):
    """Exception handling for DataService instantiation."""

    pass


class SelectionExistsError(Exception):
    """Exception handling for Dataset instantiation
    with a choice of modification, organism,
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
    """Utility class to create a dataset and import
    data records. Upon instantiation, a number of
    validation routines are called to check the
    consistency of the input parameters.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param smid: Project ID (SMID)
    :type smid: str
    :param title: Title associated with EUF/bedRMod file/dataset
    :type title: str
    :param filen: EUF/bedRMod file path
    :type filen: str | Path
    :param assembly_id: Assembly ID. This is not the
    assembly name from a EU formatted file header.
    :type assembly_id: int
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
        modification_ids: int | list[int],
        organism_id: int,
        technology_id: int,
    ) -> None:
        """Initializer method."""
        self._session = session
        self._smid = smid
        self._title = title
        self._filen = filen
        self._assembly_id = assembly_id
        self._modification_ids: list[int] = utils.to_list(modification_ids)
        self._organism_id = organism_id
        self._technology_id = technology_id

        # a dict with key: value pair as sort_name: modification_id
        self._modification_names: dict[str, int] = dict()
        self._selection_ids: list[int] = []

        self._eufid: str
        self._assembly_name: str
        self._current_assembly_name: str
        self._taxa_id: int
        self._organism_name: str

        self._validate_args()
        self._validate_selection_ids()
        self._set_from_assembly()

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
        try:
            assembly_service = AssemblyService.from_id(
                self._session, assembly_id=self._assembly_id
            )
        except AssemblyVersionError:
            assembly_service = AssemblyService.from_new(
                self._session, name=self._assembly_name, taxa_id=self._taxa_id
            )
            if assembly_service._assembly_id != self._assembly_id:
                msg = (
                    f"Mismatch in assembly versions: {self._assembly_id} and "
                    f"{assembly_service._assembly_id}. Aborting transaction!"
                )
                raise AssemblyVersionError(msg)
            is_liftover = True
        finally:
            seqids = assembly_service.get_seqids(
                organism=self._organism_name, assembly=self._current_assembly_name
            )

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
                organism_id=self._organism_id,
                technology_id=self._technology_id,
            )
            importer.header.parse_header()
            # compare input and header
            self.validate_imported("organism", self._taxa_id, importer.header.taxid)
            self.validate_imported(
                "assembly", self._assembly_name, importer.header.assembly
            )
            importer.header.close()  # flush
            # add association = (EUFID, modification)
            self._add_association()  # flush
            # instantiate data importer
            importer.init_data_importer(
                association=self._modification_names,
                seqids=seqids,
                no_flush=is_liftover,
            )
            importer.data.parse_records()
            importer.data.close(raise_missing=True)  # flush
        except:
            checkpoint.rollback()
            raise
        else:
            if is_liftover:
                msg = f"Lifting over dataset from {self._assembly_name} to {self._current_assembly_name}..."
                logger.info(msg)

                records = importer.data.get_buffer()
                # CrossMap converts BED files with less than 12 columns, for 12-columns exactly,
                # they are all updated accordingly, and it fails silently with more than 12 columns.
                records = [
                    tuple(
                        [
                            val
                            for key, val in record.items()
                            if key not in ["dataset_id", "modification_id"]
                        ]
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
        annotation_service = AnnotationService(
            session=self._session,
            bedtools_service=get_bedtools_service(),
            modification_service=get_modification_service(),
            taxa_id=self._taxa_id,
        )
        try:
            annotation_service.annotate_data(self._eufid)
            self._session.commit()
        except:
            checkpoint.rollback()
            raise
        # ... update cache
        selections = {
            idx: self._get_modification_from_selection(idx)
            for idx in self._selection_ids
        }
        annotation_service.update_gene_cache(self._eufid, selections)

        msg = (
            f"Added dataset {self._eufid} to project {self._smid} with title = {self._title}, "
            f"and the following selections: {self._selection_ids}. "
        )
        logger.info(msg)

    def get_eufid(self) -> str:
        """Return newly created EUFID.

        :returns: EUFID
        :rtype: str
        """
        return self._eufid

    def _validate_entry(self) -> None:
        """Tentatively check if dataset already exists using
        SMID, title, and selection.

        Raises DatasetExistsError.
        """
        query = (
            select(func.distinct(Dataset.id))
            .join(DatasetModificationAssociation, Dataset.associations, isouter=True)
            .where(
                Dataset.project_id == self._smid,
                Dataset.title == self._title,
                DatasetModificationAssociation.modification_id.in_(
                    self._modification_ids
                ),
                Dataset.organism_id == self._organism_id,
                Dataset.technology_id == self._technology_id,
            )
        )
        eufid = self._session.execute(query).scalar_one_or_none()
        if eufid:
            msg = (
                f"Suspected duplicate record with EUFID = {eufid} (SMID = {self._smid}), "
                f"and title = {self._title}. Aborting transaction!"
            )
            raise DatasetExistsError(msg)

    def _add_association(self) -> None:
        """Create new association entry for dataset."""
        for mid in self._modification_ids:
            association = DatasetModificationAssociation(
                dataset_id=self._eufid, modification_id=mid
            )
            self._session.add(association)
            self._session.flush()

    def _create_eufid(self) -> None:
        """Create new dataset ID."""
        query = select(Dataset.id)
        eufids = self._session.execute(query).scalars().all()
        self._eufid = utils.gen_short_uuid(self.EUFID_LENGTH, eufids)

    def _modification_id_to_name(self, idx: int) -> str:
        """Retrieve modification name for id.

        :param idx: id (PK)
        :type idx: int
        :returns: Modification short_name
        :rtype: str
        """
        query = (
            select(Modomics.short_name)
            .join(Modification, Modomics.modifications)
            .where(Modification.id == idx)
        )
        return self._session.execute(query).scalar_one()

    def _organism_id_to_organism(self, idx: int) -> tuple[str, str]:
        """Retrieve cto and organism name for id.

        :param idx: id (PK)
        :type idx: int
        :returns: CTO and Taxa (name)
        :rtype: tuple of (str, str)
        """
        query = (
            select(Organism.cto, Taxa.name)
            .join(Taxa, Organism.inst_taxa)
            .where(Organism.id == idx)
        )
        return self._session.execute(query).one()

    def _technology_id_to_tech(self, idx: int) -> str:
        """Retrieve technology name for id.

        :param idx: id (PK)
        :type idx: int
        :returns: Technology
        :rtype: str
        """
        query = select(DetectionTechnology.tech).where(DetectionTechnology.id == idx)
        return self._session.execute(query).scalar_one()

    def _get_modification_from_selection(self, idx: int) -> int:
        """Retrieve modification_id from selection_id.

        :param idx: selection ID
        :type idx: int
        :returns: Modification ID
        :rtype: int
        """
        query = select(Selection.modification_id).where(Selection.id == idx)
        return self._session.execute(query).scalar_one()

    def _validate_args(self) -> None:
        """Validate modification_id, technology_id, and
        organism_id, which make up a unique selection.
        If successful, update modification_names.

        Raises InstantiationError.
        """
        is_found = self._session.query(
            exists().where(Project.id == self._smid)
        ).scalar()
        if not is_found:
            msg = f"Unrecognised SMID {self._smid}. Cannot instantiate DataService!"
            raise InstantiationError(msg)
        if len(set(self._modification_ids)) != len(self._modification_ids):
            msg = "Repeated modification IDs. Cannot instantiate DataService!"
            raise InstantiationError(msg)
        for mid in self._modification_ids:
            try:
                mname = self._modification_id_to_name(mid)
                self._modification_names[mname] = mid
            except NoResultFound:
                msg = f"Modification ID = {mid} not found! Cannot instantiate DataService!"
                raise InstantiationError(msg)
        try:
            _ = self._technology_id_to_tech(self._technology_id)
        except NoResultFound:
            msg = f"Technology ID = {self._technology_id} not found! Cannot instantiate DataService!"
            raise InstantiationError(msg)
        try:
            _ = self._organism_id_to_organism(self._organism_id)
        except NoResultFound:
            msg = f"Organism ID = {self._organism_id} not found! Cannot instantiate DataService!"
            raise InstantiationError(msg)

    def _validate_selection_ids(self) -> None:
        """Retrieve and validate selection IDs associated with a
        dataset. Depending on the choice of modification_id(s),
        organism_id, and technology_id, a selection_id may
        or may not exists in the database. If successful, update
        selection_ids.

        Raises a SelectionExistsError if a selection_id
        does not exist. A MultipleResultsFound cannot happen,
        due to the unique index on Selection.
        """
        for mname, mid in self._modification_names.items():
            query = queries.query_column_where(
                Selection,
                "id",
                filters={
                    "modification_id": mid,
                    "technology_id": self._technology_id,
                    "organism_id": self._organism_id,
                },
            )
            try:
                self._selection_ids.append(self._session.execute(query).scalar_one())
            except NoResultFound as exc:
                tech = self._technology_id_to_tech(self._technology_id)
                cto, organism = self._organism_id_to_organism(self._organism_id)
                msg = (
                    f"Selection (mod={mname}, tech={tech}, "
                    f"organism=({organism}, {cto})) does not exists. "
                    "Aborting transaction!"
                )
                raise SelectionExistsError(msg) from exc

    def _set_from_assembly(self) -> None:
        """Retrieve and set assembly-related variables.
        Check if organism matches, else raises an InstantiationError.
        """
        query = queries.query_column_where(
            Assembly, ["name", "taxa_id"], filters={"id": self._assembly_id}
        )
        self._assembly_name, self._taxa_id = self._session.execute(query).one()
        query = queries.query_column_where(Taxa, "name", filters={"id": self._taxa_id})
        self._organism_name = self._session.execute(query).scalar_one()
        _, organism_name = self._organism_id_to_organism(self._organism_id)
        if self._organism_name != organism_name:
            msg = f"Mismatch between assembly {self._assembly_name} and organism {organism_name}. Cannot instantiate DataService!"
            raise InstantiationError(msg)
        query = queries.get_assembly_version()
        version = self._session.execute(query).scalar_one()
        query = queries.query_column_where(
            Assembly, "name", filters={"taxa_id": self._taxa_id, "version": version}
        )
        self._current_assembly_name = self._session.execute(query).scalar_one()

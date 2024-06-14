import re
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cache
from typing import List, Dict, Optional, TextIO

from sqlalchemy import select, func, exists
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from scimodom.database.buffer import InsertBuffer
from scimodom.database.database import get_session
from scimodom.database.models import (
    Assembly,
    Dataset,
    DatasetModificationAssociation,
    DetectionTechnology,
    Modomics,
    Modification,
    Organism,
    Project,
    Taxa,
    ProjectSource,
    User,
    UserProjectAssociation,
    Selection,
    AssemblyVersion,
    Data,
)
from scimodom.services.annotation import AnnotationService
from scimodom.services.assembly import AssemblyService, AssemblyVersionError
from scimodom.services.bedtools import get_bedtools_service, BedToolsService
from scimodom.services.data import get_data_service, DataService
from scimodom.utils import utils
from scimodom.utils.bed_importer import EufImporter
from scimodom.utils.bedtools_dto import EufRecord
from scimodom.utils.specifications import SPECS_EUF, EUFID_LENGTH

logger = logging.getLogger(__name__)


@dataclass
class _ImportContext:
    smid: str
    title: str
    assembly_id: int
    modification_ids: list[int]
    organism_id: int
    technology_id: int
    eufid: str

    modification_names: dict[str, int] | None = None
    selection_ids: list[int] | None = None
    assembly_name: str | None = None
    current_assembly_name: str | None = None
    taxa_id: int | None = None
    organism_name: str | None = None
    assembly_service: AssemblyService | None = None
    is_liftover: bool = False
    seqids: list[str] | None = None


class DatasetHeaderError(Exception):
    """Exception for handling mismatch between
    dataset header and input values."""

    pass


class DatasetImportError(Exception):
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


class SpecsError(Exception):
    """Exception handling for specification errors."""

    pass


def _none_if_empty(x):
    if x == "":
        return None
    else:
        return x


class DatasetService:
    FILE_FORMAT_VERSION_REGEXP = re.compile(r".*?([0-9.]+)\Z")

    def __init__(
        self,
        session: Session,
        data_service: DataService,
        bedtools_service: BedToolsService,
    ):
        self._session = session
        self._data_service = data_service
        self._bedtools_service = bedtools_service

    def get_by_id(self, eufid: str) -> Dataset:
        """Retrieve dataset by EUFID.

        :param eufid: EUFID
        :type eufid: str
        :returns: Query result
        :rtype: list of dict
        """
        return self._session.scalars(select(Dataset).where(Dataset.id == eufid)).one()

    def get_datasets(self, user: Optional[User] = None) -> List[Dict[str, str]]:
        """Retrieve all datasets. Add project-related information.

        :param user: Restricts results based on projects associated with user.
        :type user: User
        :returns: Query result
        :rtype: list of dict
        """

        query = (
            select(
                Dataset.project_id,
                Dataset.id.label("dataset_id"),
                Dataset.title.label("dataset_title"),
                Dataset.sequencing_platform,
                Dataset.basecalling,
                Dataset.bioinformatics_workflow,
                Dataset.experiment,
                Project.title.label("project_title"),
                Project.summary.label("project_summary"),
                func.group_concat(ProjectSource.doi.distinct()).label("doi"),
                func.group_concat(ProjectSource.pmid.distinct()).label("pmid"),
                Modification.rna,
                func.group_concat(Modomics.short_name.distinct()).label(
                    "modomics_sname"
                ),
                DetectionTechnology.tech,
                Taxa.short_name.label("taxa_sname"),
                Taxa.id.label("taxa_id"),
                Organism.cto,
            )
            .join_from(Dataset, Project, Dataset.inst_project)
            .join_from(
                Project,
                ProjectSource,
                Project.sources,
                isouter=True,
            )
            .join_from(Dataset, DatasetModificationAssociation, Dataset.associations)
            .join_from(
                DatasetModificationAssociation,
                Modification,
                DatasetModificationAssociation.inst_modification,
            )
            .join_from(Modification, Modomics, Modification.inst_modomics)
            .join_from(Dataset, DetectionTechnology, Dataset.inst_technology)
            .join_from(Dataset, Organism, Dataset.inst_organism)
            .join_from(Organism, Taxa, Organism.inst_taxa)
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
        query = query.group_by(Dataset.project_id, Dataset.id)
        return [row._asdict() for row in self._session.execute(query)]

    def import_dataset(
        self,
        stream: TextIO,
        source: str,
        smid: str,
        title: str,
        assembly_id: int,
        modification_ids: List[int],
        organism_id: int,
        technology_id: int,
    ) -> str:
        context = _ImportContext(
            smid=smid,
            title=title,
            assembly_id=assembly_id,
            modification_ids=modification_ids,
            organism_id=organism_id,
            technology_id=technology_id,
            eufid=self._get_eufid(),
        )
        self._sanitize_import_context(context)
        checkpoint = self._session.begin_nested()
        try:
            importer = EufImporter(stream=stream, source=source)
            headers = self._sanitize_header(importer, context)
            self._create_dataset(headers, context)
            if context.is_liftover:
                self._do_lift_over(importer, context)
            else:
                self._do_direct_import(importer, context)
            self._add_association(context)
        except Exception:
            checkpoint.rollback()
            raise
        logger.info("Annotating data now...")

        # annotate newly imported data...
        annotation_service = AnnotationService(
            session=self._session,
            bedtools_service=self._bedtools_service,
            modification_service=self._data_service,
            taxa_id=context.taxa_id,
        )
        try:
            annotation_service.annotate_data(context.eufid)
            self._session.commit()
        except Exception:
            checkpoint.rollback()
            raise
        # ... update cache
        selections = {
            idx: self._get_modification_from_selection(idx)
            for idx in context.selection_ids
        }
        annotation_service.update_gene_cache(context.eufid, selections)

        logger.info(
            f"Added dataset {context.eufid} to project {context.smid} with title = {context.title}, "
            f"and the following selections: {context.selection_ids}. "
        )
        return context.eufid

    def _sanitize_import_context(self, context):
        is_found = self._session.query(
            exists().where(Project.id == context.smid)
        ).scalar()
        if not is_found:
            raise DatasetImportError(f"Unrecognised SMID {context.smid}!")
        self._sanitize_modification_ids(context)
        try:
            _ = self._technology_id_to_tech(context.technology_id)
        except NoResultFound:
            raise DatasetImportError(
                f"Technology ID = {context.technology_id} not found!"
            )
        try:
            _ = self._organism_id_to_organism(context.organism_id)
        except NoResultFound:
            raise DatasetImportError(f"Organism ID = {context.organism_id} not found!")
        self._sanitize_selection_ids(context)
        self._check_for_duplicate_dataset(context)
        self._sanitize_assembly_data(context)

    def _sanitize_modification_ids(self, context):
        if len(set(context.modification_ids)) != len(context.modification_ids):
            raise DatasetImportError("Repeated modification IDs!")
        context.modification_names = {}
        for mid in context.modification_ids:
            try:
                mname = self._modification_id_to_name(mid)
                context.modification_names[mname] = mid
            except NoResultFound:
                raise DatasetImportError(f"Modification ID = {mid} not found!")

    def _get_eufid(self) -> str:
        """Create new dataset ID."""
        query = select(Dataset.id)
        eufids = self._session.execute(query).scalars().all()
        return utils.gen_short_uuid(EUFID_LENGTH, eufids)

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

    def _technology_id_to_tech(self, idx: int) -> str:
        """Retrieve technology name for id.

        :param idx: id (PK)
        :type idx: int
        :returns: Technology
        :rtype: str
        """
        query = select(DetectionTechnology.tech).where(DetectionTechnology.id == idx)
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
        row = self._session.execute(query).one()
        return row.cto, row.name

    def _sanitize_selection_ids(self, context):
        """Retrieve and validate selection IDs associated with a
        dataset. Depending on the choice of modification_id(s),
        organism_id, and technology_id, a selection_id may
        or may not exists in the database. If successful, update
        selection_ids.
        """
        context.selection_ids = []
        for mname, mid in context.modification_names.items():
            query = select(Selection.id).filter_by(
                modification_id=mid,
                technology_id=context.technology_id,
                organism_id=context.organism_id,
            )
            try:
                selection_id = self._session.execute(query).scalar_one()
                context.selection_ids.append(selection_id)
            except NoResultFound:
                tech = self._technology_id_to_tech(context.technology_id)
                cto, organism = self._organism_id_to_organism(context.organism_id)
                raise SelectionExistsError(
                    f"Selection (mod={mname}, tech={tech}, "
                    f"organism=({organism}, {cto})) does not exists!"
                )

    def _check_for_duplicate_dataset(self, context):
        eufid = self._session.execute(
            select(func.distinct(Dataset.id))
            .join(DatasetModificationAssociation, Dataset.associations, isouter=True)
            .where(
                Dataset.project_id == context.smid,
                Dataset.title == context.title,
                DatasetModificationAssociation.modification_id.in_(
                    context.modification_ids
                ),
                Dataset.organism_id == context.organism_id,
                Dataset.technology_id == context.technology_id,
            )
        ).scalar_one_or_none()
        if eufid:
            msg = (
                f"Suspected duplicate record with EUFID = {eufid} (SMID = {context.smid}), "
                f"and title = {context.title}."
            )
            raise DatasetExistsError(msg)

    def _sanitize_assembly_data(self, context):
        assembly_name, taxa_id = self._session.execute(
            select(Assembly.name, Assembly.taxa_id).filter_by(id=context.assembly_id)
        ).one()
        context.assembly_name = assembly_name
        context.taxa_id = taxa_id
        context.organism_name = self._session.execute(
            select(Taxa.name).filter_by(id=taxa_id)
        ).scalar_one()
        _, organism_name = self._organism_id_to_organism(context.organism_id)
        if context.organism_name != organism_name:
            raise DatasetImportError(
                f"Mismatch between assembly {assembly_name} and organism {organism_name}!"
            )
        context.current_assembly_name = self._session.execute(
            select(Assembly.name)
            .join(AssemblyVersion, Assembly.version == AssemblyVersion.version_num)
            .where(Assembly.taxa_id == taxa_id)
        ).scalar_one()
        try:
            assembly_service = AssemblyService.from_id(
                self._session, assembly_id=context.assembly_id
            )
        except AssemblyVersionError:
            assembly_service = AssemblyService.from_new(
                self._session, name=context.assembly_name, taxa_id=context.taxa_id
            )
            if assembly_service._assembly_id != context.assembly_id:
                raise AssemblyVersionError(
                    f"Mismatch in assembly versions: {context.assembly_id} and "
                    f"{assembly_service._assembly_id}"
                )
            context.is_liftover = True
        context.assembly_service = assembly_service
        context.seqids = assembly_service.get_seqids(
            organism_name, context.current_assembly_name
        )

    def _sanitize_header(self, importer, context):
        file_format = importer.get_header("fileformat")
        match = self.FILE_FORMAT_VERSION_REGEXP.match(file_format)
        if match is None:
            raise SpecsError("Failed to parse version from header")
        version = match.group(1)
        if version not in SPECS_EUF["versions"]:
            raise SpecsError(f"Unknown or outdated version {version}")
        spec = SPECS_EUF[version]

        result = {}
        for header, internal_name in spec["headers"].items():
            value = importer.get_header(header)
            if value is None:
                raise SpecsError(f"Required header '{header} is missing")
            result[internal_name] = value

        for header in spec["required"]:
            if importer.get_header(header) == "":
                raise SpecsError(f"Required header '{header} is empty")
        for name, form_value, header_value in [
            ("organism", context.taxa_id, result["taxa_id"]),
            ("assembly", context.assembly_name, result["assembly_id"]),
        ]:
            if str(form_value) != header_value:
                raise DatasetHeaderError(
                    f"Expected {form_value} for {name}; got {header_value} (file header). "
                    f"Aborting transaction!"
                )
        return result

    def _create_dataset(self, headers, context):
        dataset = Dataset(
            id=context.eufid,
            project_id=context.smid,
            organism_id=context.organism_id,
            technology_id=context.technology_id,
            title=context.title,
            date_added=datetime.now(timezone.utc),
            modification_type=headers["modification_type"],
            sequencing_platform=_none_if_empty(headers["sequencing_platform"]),
            basecalling=_none_if_empty(headers["basecalling"]),
            bioinformatics_workflow=_none_if_empty(headers["bioinformatics_workflow"]),
            experiment=_none_if_empty(headers["experiment"]),
            external_source=_none_if_empty(headers["external_source"]),
        )
        self._session.add(dataset)

    def _do_direct_import(self, importer, context):
        with InsertBuffer[Data](self._session) as buffer:
            for record in importer.parse():
                if self._check_euf_record(record, importer, context):
                    data = self._get_data_record(record, context)
                    buffer.queue(data)

    @staticmethod
    def _check_euf_record(record, importer, context):
        if record.chrom not in context.seqids:
            importer.report_error(
                f"Unrecognized chrom: {record.chrom}. Ignore this warning "
                "for scaffolds and contigs, otherwise this could be due to misformatting!"
            )
            return False
        if record.name not in context.modification_names:
            importer.report_error(f"Unrecognized name: {record.name}.")
            return False
        return True

    @staticmethod
    def _get_data_record(record: EufRecord, context):
        return Data(
            dataset_id=context.eufid,
            modification_id=context.modification_names.get(record.name),
            chrom=record.chrom,
            start=record.start,
            end=record.end,
            name=record.name,
            score=record.score,
            strand=record.strand.value,
            thick_start=record.thick_start,
            thick_end=record.thick_end,
            item_rgb=record.item_rgb,
            coverage=record.coverage,
            frequency=record.frequency,
        )

    def _do_lift_over(self, importer, context):
        def generator():
            for record in importer.parse():
                if self._check_euf_record(record, importer, context):
                    yield record

        logger.info(
            f"Lifting over dataset from {context.assembly_name} to {context.current_assembly_name}..."
        )
        raw_file = self._bedtools_service.create_temp_euf_file(generator())
        lifted_file = context.assembly_service.liftover(raw_file)
        with open(lifted_file) as fp:
            lifted_importer = EufImporter(stream=fp, source=lifted_file)
            self._do_direct_import(lifted_importer, context)

    def _add_association(self, context) -> None:
        """Create new association entry for dataset."""
        for mid in context.modification_ids:
            association = DatasetModificationAssociation(
                dataset_id=context.eufid, modification_id=mid
            )
            self._session.add(association)
            self._session.flush()

    def _get_modification_from_selection(self, idx: int) -> int:
        """Retrieve modification_id from selection_id.

        :param idx: selection ID
        :type idx: int
        :returns: Modification ID
        :rtype: int
        """
        query = select(Selection.modification_id).where(Selection.id == idx)
        return self._session.execute(query).scalar_one()


@cache
def get_dataset_service() -> DatasetService:
    """Helper function to set up a DatasetService object by injecting its dependencies.

    :returns: Dataset service instance
    :rtype: DatasetService
    """
    return DatasetService(
        session=get_session(),
        data_service=get_data_service(),
        bedtools_service=get_bedtools_service(),
    )

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cache
import logging
import re
from typing import List, Dict, Optional, TextIO

from sqlalchemy import select, func, exists, delete
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from scimodom.database.buffer import InsertBuffer
from scimodom.database.database import get_session
from scimodom.database.models import (
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
    Data,
    DataAnnotation,
)
from scimodom.services.annotation import get_annotation_service, AnnotationService
from scimodom.services.assembly import (
    get_assembly_service,
    AssemblyService,
)
from scimodom.services.bedtools import get_bedtools_service, BedToolsService
from scimodom.services.file import FileService, get_file_service
from scimodom.utils.importer.bed_importer import EufImporter
from scimodom.utils.dtos.bedtools import EufRecord
from scimodom.utils.specs.euf import (
    EUF_COMPATIBLE_VERSIONS,
    EUF_HEADERS,
    EUF_REQUIRED_HEADERS,
)
from scimodom.utils.specs.enums import AnnotationSource, Identifiers
from scimodom.utils.utils import gen_short_uuid

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
    annotation_source: AnnotationSource
    dry_run_flag: bool
    update_flag: bool

    modification_names: dict[str, int] | None = None
    selection_ids: list[int] | None = None
    is_liftover: bool = False
    seqids: list[str] | None = None


class DatasetHeaderError(Exception):
    """Exception for handling mismatch between
    dataset header and input values."""

    pass


class DatasetImportError(Exception):
    pass


class SelectionNotFoundError(Exception):
    """Exception handling for Dataset instantiation
    with a choice of modification, organism,
    and technology that does not exists."""

    pass


class DatasetExistsError(Exception):
    """Exception for handling Dataset instantiation,
    e.g. suspected duplicate entries."""

    pass


class DatasetUpdateError(Exception):
    """Exception for handling data records
    update for existing dataset."""

    pass


class SpecsError(Exception):
    """Exception handling for specification errors."""

    pass


class DatasetService:
    FILE_FORMAT_VERSION_REGEXP = re.compile(r".*?([0-9.]+)\Z")

    def __init__(
        self,
        session: Session,
        file_service: FileService,
        bedtools_service: BedToolsService,
        assembly_service: AssemblyService,
        annotation_service: AnnotationService,
    ):
        self._session = session
        self._file_service = file_service
        self._bedtools_service = bedtools_service
        self._assembly_service = assembly_service
        self._annotation_service = annotation_service

    def get_by_id(self, eufid: str) -> Dataset:
        """Retrieve dataset by EUFID.

        :param eufid: EUFID
        :type eufid: str
        :returns: Dataset instance
        :rtype: Dataset
        """
        return self._session.get_one(Dataset, eufid)

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
        modification_ids: list[int],
        organism_id: int,
        technology_id: int,
        annotation_source: AnnotationSource,
        dry_run_flag: bool = False,
        eufid: str | None = None,
    ) -> str:
        """Import dataset and records from bedRMod formatted file.

        :param stream: Input stream
        :type stream: TextIO
        :param source: Import file name
        :type source: str
        :param smid: Project SMID
        :type smid: str
        :param title: Datatset title
        :type title: str
        :param assembly_id: Assembly ID
        :type assembly_id: int
        :param modification_ids: Modification ID(s)
        :type modification_ids: list[int]
        :param organism_id: Organism ID
        :type organism_id: int
        :param technology_id: Technology ID
        :type technology_id: int
        :param annotation_source: Source of annotation
        :type annotation_source: AnnotationSource
        :param dry_run_flag: Mock import if true - validate data w/o changing the database. Default is False.
        :type dry_run_flag: bool
        :param eufid: Update data and data annotation records for this EUFID (dataset). This is silently
        ignored if 'dry_run_flag' is set. Default is None.
        :type eufid: str | None
        :returns: EUFID - in case of a dry run the value 'DRYRUNDRYRUN' is returned.
        :rtype: str
        """
        update_flag = False
        if dry_run_flag:
            eufid = "DRYRUNDRYRUN"
        elif eufid is not None:
            try:
                self._session.get_one(Dataset, eufid)
            except NoResultFound:
                raise DatasetUpdateError(f"No such dataset: '{eufid}'.")
            update_flag = True
        else:
            eufid = self._generate_eufid()

        context = _ImportContext(
            smid=smid,
            title=title,
            assembly_id=assembly_id,
            modification_ids=modification_ids,
            organism_id=organism_id,
            technology_id=technology_id,
            annotation_source=annotation_source,
            eufid=eufid,
            dry_run_flag=dry_run_flag,
            update_flag=update_flag,
        )
        self._sanitize_import_context(context)

        checkpoint = None
        if not dry_run_flag:
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
            if not dry_run_flag:
                organism = self._get_organism(context.organism_id)
                self._annotation_service.annotate_data(
                    taxa_id=organism.taxa_id,
                    annotation_source=context.annotation_source,
                    eufid=context.eufid,
                    selection_ids=context.selection_ids,
                )
                self._session.commit()
        except Exception:
            if checkpoint is not None:
                checkpoint.rollback()
            raise

        logger.info(
            f"Added dataset {context.eufid} to project {context.smid} with title = {context.title}, "
            f"and the following selections: {context.selection_ids}. "
        )
        return context.eufid

    def delete_dataset(self, dataset: Dataset) -> None:
        """Delete a dataset and all associated data.

        Delete from the following tables:
        - data_annotation
        - data
        - dataset_modification_association
        - bam_file
        - dataset

        Associated BAM files are deleted from
        the file system.

        :param dataset: Dataset instance to delete
        :type dataset: Dataset
        """
        try:
            self._delete_data_records(dataset.id)
            self._session.execute(
                delete(DatasetModificationAssociation).filter_by(dataset_id=dataset.id)
            )
            bam_list = self._file_service.get_bam_file_list(dataset)
            for bam in bam_list:
                bam_file = self._file_service.get_bam_file(
                    dataset, bam["original_file_name"]
                )
                self._file_service.remove_bam_file(bam_file)
            self._session.delete(dataset)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

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
            strand=record.strand,
            thick_start=record.thick_start,
            thick_end=record.thick_end,
            item_rgb=record.item_rgb,
            coverage=record.coverage,
            frequency=record.frequency,
        )

    def _sanitize_import_context(self, context):
        is_found = self._session.query(
            exists().where(Project.id == context.smid)
        ).scalar()
        if not is_found:
            raise DatasetImportError(f"No such SMID: {context.smid}.")
        self._sanitize_modification_ids(context)
        try:
            _ = self._get_technology(context.technology_id)
        except NoResultFound:
            raise DatasetImportError(f"No such technology ID: {context.technology_id}.")
        try:
            _ = self._get_organism(context.organism_id)
        except NoResultFound:
            raise DatasetImportError(f"No such organism ID: {context.organism_id}.")
        self._sanitize_selection_ids(context)
        self._check_for_duplicate_dataset(context)
        self._sanitize_assembly(context)

    def _sanitize_modification_ids(self, context):
        if len(set(context.modification_ids)) != len(context.modification_ids):
            raise DatasetImportError("Repeated modification IDs.")
        context.modification_names = {}
        for mid in context.modification_ids:
            try:
                mname = self._modification_id_to_name(mid)
                context.modification_names[mname] = mid
            except NoResultFound:
                raise DatasetImportError(f"No such modification ID: {mid}.")
        if not self._annotation_service.check_annotation_source(
            context.annotation_source, context.modification_ids
        ):
            raise DatasetImportError("Inconsistent source!")

    def _generate_eufid(self) -> str:
        eufids = self._session.execute(select(Dataset.id)).scalars().all()
        return gen_short_uuid(Identifiers.EUFID.length, eufids)

    def _modification_id_to_name(self, idx: int) -> str:
        return self._session.execute(
            select(Modomics.short_name)
            .join(Modification, Modomics.modifications)
            .where(Modification.id == idx)
        ).scalar_one()

    def _get_technology(self, idx: int) -> DetectionTechnology:
        return self._session.get_one(DetectionTechnology, idx)

    def _get_organism(self, idx: int) -> Organism:
        return self._session.get_one(Organism, idx)

    def _sanitize_selection_ids(self, context):
        """Retrieve and validate selection IDs associated with a
        dataset. Depending on the choice of modification_id(s),
        organism_id, and technology_id, a selection_id may
        or may not exists in the database.
        """
        context.selection_ids = []
        for mname, mid in context.modification_names.items():
            try:
                selection_id = self._session.execute(
                    select(Selection.id).filter_by(
                        modification_id=mid,
                        technology_id=context.technology_id,
                        organism_id=context.organism_id,
                    )
                ).scalar_one()
                context.selection_ids.append(selection_id)
            except NoResultFound:
                technology = self._get_technology(context.technology_id)
                organism = self._get_organism(context.organism_id)
                raise SelectionNotFoundError(
                    f"No such selection with {mname}, {technology.tech}, and "
                    f"{organism.cto} ({organism.taxa_id})."
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
        if context.update_flag:
            if eufid != context.eufid:
                raise DatasetUpdateError(
                    f"Provided dataset '{context.eufid}', but found '{eufid}' with "
                    f"title '{context.title}' (SMID '{context.smid}')."
                )
        else:
            if eufid:
                raise DatasetExistsError(
                    f"Suspected duplicate dataset '{eufid}' (SMID '{context.smid}'), "
                    f"and title '{context.title}'."
                )

    def _sanitize_assembly(self, context):
        assembly = self._assembly_service.get_assembly_by_id(context.assembly_id)
        organism = self._get_organism(context.organism_id)
        if assembly.taxa_id != organism.taxa_id:
            raise DatasetImportError(
                f"No such assembly {assembly.name} for organism {organism.taxa_id}."
            )
        context.is_liftover = not self._assembly_service.is_latest_assembly(assembly)
        context.seqids = self._assembly_service.get_seqids(assembly.taxa_id)

    def _sanitize_header(self, importer, context):
        file_format = importer.get_header("fileformat")
        if file_format is None:
            raise SpecsError("Failed to parse version from header (1).")
        match = self.FILE_FORMAT_VERSION_REGEXP.match(file_format)
        if match is None:
            raise SpecsError("Failed to parse version from header (2).")
        version = match.group(1)
        if version not in EUF_COMPATIBLE_VERSIONS:
            raise SpecsError(f"Unknown or outdated version {version}.")

        result = {}
        for header, internal_name in EUF_HEADERS.items():
            value = importer.get_header(header)
            if value is None:
                raise SpecsError(f"Required header '{header}' is missing.")
            result[internal_name] = value

        assembly = self._assembly_service.get_assembly_by_id(context.assembly_id)
        for header in EUF_REQUIRED_HEADERS:
            value = importer.get_header(header)
            if value is None or value == "":
                raise SpecsError(f"Required header '{header}' is empty.")
        for name, form_value, header_value in [
            ("organism", assembly.taxa_id, result["taxa_id"]),
            ("assembly", assembly.name, result["assembly_name"]),
        ]:
            if str(form_value) != header_value:
                raise DatasetHeaderError(
                    f"Expected {form_value} for {name}; got {header_value} from file header."
                )
        return result

    def _create_dataset(self, headers, context):
        if context.update_flag or context.dry_run_flag:
            return
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
        self._session.flush()

    def _do_direct_import(self, importer, context):
        if context.dry_run_flag:
            for record in importer.parse():
                if self._check_euf_record(record, importer, context):
                    self._get_data_record(record, context)
        else:
            if context.update_flag:
                self._delete_data_records(context.eufid)
            with InsertBuffer[Data](self._session) as buffer:
                for record in importer.parse():
                    if self._check_euf_record(record, importer, context):
                        data = self._get_data_record(record, context)
                        buffer.queue(data)

    def _delete_data_records(self, eufid: str):
        data_ids_to_delete = (
            self._session.execute(select(Data.id).filter_by(dataset_id=eufid))
            .scalars()
            .all()
        )
        self._session.execute(
            delete(DataAnnotation).where(DataAnnotation.data_id.in_(data_ids_to_delete))
        )
        self._session.execute(delete(Data).filter_by(dataset_id=eufid))

    def _do_lift_over(self, importer, context):
        def generator():
            for record in importer.parse():
                if self._check_euf_record(record, importer, context):
                    yield record

        assembly = self._assembly_service.get_assembly_by_id(context.assembly_id)
        current_assembly_name = self._assembly_service.get_name_for_version(
            assembly.taxa_id
        )
        logger.info(
            f"Lifting over dataset from {assembly.name} to {current_assembly_name}..."
        )
        raw_file = self._bedtools_service.create_temp_euf_file(generator())
        lifted_file = self._assembly_service.liftover(assembly, raw_file)
        with open(lifted_file) as fp:
            lifted_importer = EufImporter(stream=fp, source=lifted_file)
            self._do_direct_import(lifted_importer, context)

    def _add_association(self, context) -> None:
        if context.update_flag or context.dry_run_flag:
            return
        for mid in context.modification_ids:
            association = DatasetModificationAssociation(
                dataset_id=context.eufid, modification_id=mid
            )
            self._session.add(association)
        self._session.flush()


def _none_if_empty(x):
    if x == "":
        return None
    else:
        return x


@cache
def get_dataset_service() -> DatasetService:
    """Helper function to set up a DatasetService object by injecting its dependencies.

    :returns: Dataset service instance
    :rtype: DatasetService
    """

    return DatasetService(
        session=get_session(),
        file_service=get_file_service(),
        bedtools_service=get_bedtools_service(),
        assembly_service=get_assembly_service(),
        annotation_service=get_annotation_service(),
    )

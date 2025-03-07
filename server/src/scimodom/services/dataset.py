from datetime import datetime, timezone
from functools import cache
import logging
from typing import List, Dict, Optional, TextIO

from sqlalchemy import select, func, delete
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
    Data,
    DataAnnotation,
)
from scimodom.services.annotation import get_annotation_service, AnnotationService
from scimodom.services.file import FileService, get_file_service
from scimodom.services.validator import (
    _DatasetImportContext,
    DatasetUpdateError,
    ValidatorService,
    get_validator_service,
)
from scimodom.utils.importer.bed_importer import EufImporter
from scimodom.utils.dtos.bedtools import EufRecord
from scimodom.utils.specs.enums import AnnotationSource, Identifiers
from scimodom.utils.utils import gen_short_uuid

logger = logging.getLogger(__name__)


class DatasetService:
    """Provides methods to retrieve and manage
    datasets and related data.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param annotation_service: Annotation service instance
    :type annotation_service: AnnotationService
    :param file_service: File service instance
    :type file_service: FileService
    :param validator_service: Validator service instance
    :type validator_service: ValidatorService
    """

    def __init__(
        self,
        session: Session,
        annotation_service: AnnotationService,
        file_service: FileService,
        validator_service: ValidatorService,
    ):
        self._session = session
        self._annotation_service = annotation_service
        self._file_service = file_service
        self._validator_service = validator_service

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
        """Import dataset and records from bedRMod formatted file
        and write into the database.

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
        :param dry_run_flag: If true, validate data w/o writing into the database. Default is False.
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

        checkpoint = None
        if not dry_run_flag:
            checkpoint = self._session.begin_nested()
        try:
            importer = EufImporter(stream=stream, source=source)
            self._validator_service.create_import_context(
                importer=importer,
                smid=smid,
                eufid=eufid,
                title=title,
                modification_ids=modification_ids,
                organism_id=organism_id,
                technology_id=technology_id,
                assembly_id=assembly_id,
                annotation_source=annotation_source,
                dry_run_flag=dry_run_flag,
                update_flag=update_flag,
            )
            self._import_dataset_with_context(importer)
        except Exception:
            if checkpoint is not None:
                checkpoint.rollback()
            raise

        return eufid

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
    def _get_data_record(record: EufRecord, context: _DatasetImportContext):
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

    def _generate_eufid(self) -> str:
        eufids = self._session.execute(select(Dataset.id)).scalars().all()
        return gen_short_uuid(Identifiers.EUFID.length, eufids)

    def _import_dataset_with_context(self, importer: EufImporter) -> None:
        context = self._validator_service.get_import_context()
        if context is not None:
            self._create_dataset(context)
            self._import_data_records(context, importer)
            self._add_association(context)
            if not context.dry_run_flag:
                self._annotation_service.annotate_data(
                    taxa_id=context.taxa_id,
                    annotation_source=context.annotation_source,
                    eufid=context.eufid,
                    selection_ids=context.selection_ids,
                )
                self._session.commit()

                logger.info(
                    f"Added dataset {context.eufid} to project {context.smid} with title = {context.title}, "
                    f"and the following selections: {context.selection_ids}. "
                )

    def _create_dataset(self, context: _DatasetImportContext):
        if context.update_flag or context.dry_run_flag:
            return
        header = self._validator_service.get_validated_header()
        if header is not None:
            dataset = Dataset(
                id=context.eufid,
                project_id=context.smid,
                organism_id=context.organism_id,
                technology_id=context.technology_id,
                title=context.title,
                date_added=datetime.now(timezone.utc),
                modification_type=header["modification_type"],
                sequencing_platform=_none_if_empty(header["sequencing_platform"]),
                basecalling=_none_if_empty(header["basecalling"]),
                bioinformatics_workflow=_none_if_empty(
                    header["bioinformatics_workflow"]
                ),
                experiment=_none_if_empty(header["experiment"]),
                external_source=_none_if_empty(header["external_source"]),
            )
            self._session.add(dataset)
            self._session.flush()

    def _import_data_records(
        self, context: _DatasetImportContext, importer: EufImporter
    ):
        if context.dry_run_flag:
            for record in self._validator_service.get_validated_records(
                importer, context
            ):
                self._get_data_record(record, context)
        else:
            if context.update_flag:
                self._delete_data_records(context.eufid)
            with InsertBuffer[Data](self._session) as buffer:
                for record in self._validator_service.get_validated_records(
                    importer, context
                ):
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

    def _add_association(self, context: _DatasetImportContext) -> None:
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
        annotation_service=get_annotation_service(),
        file_service=get_file_service(),
        validator_service=get_validator_service(),
    )

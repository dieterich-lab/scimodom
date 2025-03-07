from dataclasses import dataclass, field
from functools import cache
import logging
import re
from typing import Generator

from sqlalchemy import select, func, exists
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Dataset,
    DatasetModificationAssociation,
    DetectionTechnology,
    Modomics,
    Modification,
    Organism,
    Project,
    Selection,
)
from scimodom.services.annotation import get_annotation_service, AnnotationService
from scimodom.services.assembly import (
    AssemblyNotFoundError,
    get_assembly_service,
    AssemblyService,
)
from scimodom.services.bedtools import get_bedtools_service, BedToolsService
from scimodom.utils.importer.bed_importer import EufImporter
from scimodom.utils.dtos.bedtools import EufRecord
from scimodom.utils.specs.euf import (
    EUF_COMPATIBLE_VERSIONS,
    EUF_HEADERS,
    EUF_REQUIRED_HEADERS,
)
from scimodom.utils.specs.enums import AnnotationSource

logger = logging.getLogger(__name__)


@dataclass
class _ReadOnlyImportContext:
    taxa_id: int
    assembly_id: int

    is_liftover: bool = False
    seqids: list[str] = field(default_factory=list)
    modification_names: dict[str, int] = field(default_factory=dict)


@dataclass(kw_only=True)
class _DatasetImportContext(_ReadOnlyImportContext):
    smid: str
    eufid: str
    title: str
    modification_ids: list[int]
    organism_id: int
    technology_id: int
    annotation_source: AnnotationSource
    dry_run_flag: bool
    update_flag: bool

    selection_ids: list[int] = field(default_factory=list)


class SpecsError(Exception):
    """Exception for handling specification errors."""

    pass


class DatasetHeaderError(Exception):
    """Exception for handling mismatch between
    dataset header and input values."""

    pass


class DatasetImportError(Exception):
    """Exception for handling general import
    errors associated with the import context."""

    pass


class SelectionNotFoundError(Exception):
    """Exception for handling Dataset instantiation
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


class ValidatorService:
    """Provide a validator service for data import.

    Provide an import context and helper methods to
    perform validation and, where relevant, lift over
    during data import (EU-formatted or bedRMod files).

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param annotation_service: Annotation service instance
    :type annotation_service: AnnotationService
    :param assembly_service: Assembly service instance
    :type assembly_service: AssemblyService
    :param bedtools_service: BedTools service instance
    :type bedtools_service: BedToolsService
    :param data_service: Data service instance
    :type data service: DataService
    """

    FILE_FORMAT_VERSION_REGEXP = re.compile(r".*?([0-9.]+)\Z")

    def __init__(
        self,
        session: Session,
        annotation_service: AnnotationService,
        assembly_service: AssemblyService,
        bedtools_service: BedToolsService,
    ):
        self._session = session
        self._annotation_service = annotation_service
        self._assembly_service = assembly_service
        self._bedtools_service = bedtools_service

        self._ro_context: _ReadOnlyImportContext
        self._context: _DatasetImportContext
        self._read_header: dict[str, str]

    def create_read_only_import_context(
        self, importer: EufImporter, taxa_id: int, **kwargs
    ) -> None:
        """Create a minimal context for data import.

        To be used for importing data when writing
        to the database is not intended. This is used
        e.g. to import data for the Comparison View.

        Assemblies are added on the fly, in the unlikely
        case that one is missing. This should not happen
        in general, and in particular this should not happen
        for the current assembly.

        :param importer: BED importer
        :type importer: EufImporter
        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        """
        self._sanitize_header(importer)
        self._sanitize_taxa_id(taxa_id)
        assembly_name = self._read_header["assembly_name"]
        try:
            assembly = self._assembly_service.get_by_taxa_and_name(
                taxa_id, assembly_name
            )
        except NoResultFound:
            try:
                self._assembly_service.add_assembly(taxa_id, assembly_name)
                assembly = self._assembly_service.get_by_taxa_and_name(
                    taxa_id, assembly_name
                )
            except AssemblyNotFoundError as exc:
                raise DatasetImportError(exc)
        kwargs = {**kwargs, "taxa_id": taxa_id, "assembly_id": assembly.id}
        self._ro_context = _ReadOnlyImportContext(**kwargs)
        self._sanitize_read_only_import_context()

    def create_import_context(self, importer: EufImporter, **kwargs) -> None:
        """Create and validate import context.

        To be used for importing data into the database.

        :param importer: BED importer
        :type importer: EufImporter
        """
        self._sanitize_header(importer)
        taxa_id = self._get_validated_taxa_id(
            kwargs["assembly_id"], kwargs["organism_id"]
        )
        kwargs = {**kwargs, "taxa_id": taxa_id}
        self._context = _DatasetImportContext(**kwargs)
        self._sanitize_import_context()

    def get_read_only_context(self) -> _ReadOnlyImportContext | None:
        """Return read-only context if exists.

        :returns: Read-only context
        :rtype: _ReadOnlyImportContext | None
        """
        try:
            return self._ro_context
        except AttributeError:
            return None

    def get_import_context(self) -> _DatasetImportContext | None:
        """Return dataset import context if exists.

        :returns: Dataset import context
        :rtype: _DatasetImportContext | None
        """
        try:
            return self._context
        except AttributeError:
            return None

    def get_validated_header(self) -> dict[str, str] | None:
        """Return imported header as dict if exists.

        :returns: bedRMod header as dict
        :rtype: ditc[str, str] | None
        """
        try:
            return self._read_header
        except AttributeError:
            return None

    def get_validated_records(
        self,
        importer: EufImporter,
        context: _ReadOnlyImportContext | _DatasetImportContext,
    ) -> Generator[EufRecord, None, None]:
        """Parse, eventually lift over, and return records.

        This method provides additional validation, i.e. in
        addition to model validation performed by the importer.

        :param importer: BED importer
        :type importer: EufImporter
        :param context: Import context
        :type 2context: _ReadOnlyImportContext | _DatasetImportContext
        """
        if context.is_liftover:
            for record in self._do_lift_over(importer, context):
                yield record
        else:
            for record in self._do_direct_import(importer, context):
                yield record

    @staticmethod
    def _check_euf_record(record, importer, context) -> bool:
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

    def _sanitize_header(
        self,
        importer: EufImporter,
    ) -> None:
        file_format = importer.get_header("fileformat")
        if file_format is None:
            raise SpecsError("Failed to parse version from header (1).")
        match = self.FILE_FORMAT_VERSION_REGEXP.match(file_format)
        if match is None:
            raise SpecsError("Failed to parse version from header (2).")
        version = match.group(1)
        if version not in EUF_COMPATIBLE_VERSIONS:
            raise SpecsError(f"Unknown or outdated version {version}.")

        read_header = {}
        for header_tag, internal_name in EUF_HEADERS.items():
            value = importer.get_header(header_tag)
            if value is None:
                raise SpecsError(f"Required header '{header_tag}' is missing.")
            if header_tag in EUF_REQUIRED_HEADERS and value == "":
                raise SpecsError(f"Required header '{header_tag}' is empty.")
            read_header[internal_name] = value
        self._read_header = read_header

    def _sanitize_taxa_id(self, input_taxa_id: int) -> None:
        taxa_id = self._read_header["taxa_id"]
        if taxa_id != str(input_taxa_id):
            raise DatasetHeaderError(
                f"Expected {input_taxa_id} for 'organism'; got {taxa_id} from file header."
            )

    def _sanitize_assembly(
        self, context: _ReadOnlyImportContext | _DatasetImportContext
    ) -> tuple[bool, list[str]]:
        assembly = self._assembly_service.get_by_id(context.assembly_id)
        assembly_name = self._read_header["assembly_name"]
        if assembly.name != assembly_name:
            raise DatasetHeaderError(
                f"Expected {assembly.name} for 'assembly'; got {assembly_name} from file header."
            )
        is_liftover = not self._assembly_service.is_latest_assembly(assembly)
        seqids = context.seqids
        if not seqids:
            seqids = self._assembly_service.get_seqids(assembly.taxa_id)
        return is_liftover, seqids

    def _sanitize_read_only_import_context(self) -> None:
        self._ro_context.is_liftover, self._ro_context.seqids = self._sanitize_assembly(
            self._ro_context
        )
        modification_names = (
            self._session.execute(select(Modomics.short_name)).scalars().all()
        )
        # dict value (int) unused for read-only import context
        self._ro_context.modification_names = {
            name: hash(name) for name in modification_names
        }

    def _sanitize_import_context(self) -> None:
        self._context.is_liftover, self._context.seqids = self._sanitize_assembly(
            self._context
        )
        is_found = self._session.query(
            exists().where(Project.id == self._context.smid)
        ).scalar()
        if not is_found:
            raise DatasetImportError(f"No such SMID: {self._context.smid}.")
        self._sanitize_modification_ids()
        try:
            _ = self._get_technology(self._context.technology_id)
        except NoResultFound:
            raise DatasetImportError(
                f"No such technology ID: {self._context.technology_id}."
            )
        self._sanitize_selection_ids()
        self._check_for_duplicate_dataset()

    def _sanitize_modification_ids(self) -> None:
        if len(set(self._context.modification_ids)) != len(
            self._context.modification_ids
        ):
            raise DatasetImportError("Repeated modification IDs.")
        for mid in self._context.modification_ids:
            try:
                mname = self._modification_id_to_name(mid)
                self._context.modification_names[mname] = mid
            except NoResultFound:
                raise DatasetImportError(f"No such modification ID: {mid}.")
        if not self._annotation_service.check_annotation_source(
            self._context.annotation_source, self._context.modification_ids
        ):
            raise DatasetImportError("Inconsistent source!")

    def _sanitize_selection_ids(self) -> None:
        """Retrieve and validate selection IDs associated with a
        dataset. Depending on the choice of modification_id(s),
        organism_id, and technology_id, a selection_id may
        or may not exists in the database.
        """
        for mname, mid in self._context.modification_names.items():
            try:
                selection_id = self._session.execute(
                    select(Selection.id).filter_by(
                        modification_id=mid,
                        technology_id=self._context.technology_id,
                        organism_id=self._context.organism_id,
                    )
                ).scalar_one()
                self._context.selection_ids.append(selection_id)
            except NoResultFound:
                technology = self._get_technology(self._context.technology_id)
                organism = self._get_organism(self._context.organism_id)
                raise SelectionNotFoundError(
                    f"No such selection with {mname}, {technology.tech}, and "
                    f"{organism.cto} ({organism.taxa_id})."
                )

    def _check_for_duplicate_dataset(self) -> None:
        eufid = self._session.execute(
            select(func.distinct(Dataset.id))
            .join(DatasetModificationAssociation, Dataset.associations, isouter=True)
            .where(
                Dataset.project_id == self._context.smid,
                Dataset.title == self._context.title,
                DatasetModificationAssociation.modification_id.in_(
                    self._context.modification_ids
                ),
                Dataset.organism_id == self._context.organism_id,
                Dataset.technology_id == self._context.technology_id,
            )
        ).scalar_one_or_none()
        if self._context.update_flag:
            if eufid != self._context.eufid:
                raise DatasetUpdateError(
                    f"Provided dataset '{self._context.eufid}', but found '{eufid}' with "
                    f"title '{self._context.title}' (SMID '{self._context.smid}')."
                )
        else:
            if eufid:
                raise DatasetExistsError(
                    f"Suspected duplicate dataset '{eufid}' (SMID '{self._context.smid}'), "
                    f"and title '{self._context.title}'."
                )

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

    def _get_validated_taxa_id(self, assembly_id: int, organism_id: int) -> int:
        try:
            assembly = self._assembly_service.get_by_id(assembly_id)
        except NoResultFound:
            raise DatasetImportError(f"No such assembly ID: {assembly_id}.")
        try:
            organism = self._get_organism(organism_id)
        except NoResultFound:
            raise DatasetImportError(f"No such organism ID: {organism_id}.")
        if assembly.taxa_id != organism.taxa_id:
            raise DatasetImportError(
                f"No such assembly {assembly.name} for organism {organism.taxa_id}."
            )
        taxa_id = assembly.taxa_id
        self._sanitize_taxa_id(taxa_id)
        return taxa_id

    def _do_direct_import(
        self,
        importer: EufImporter,
        context: _ReadOnlyImportContext | _DatasetImportContext,
    ) -> Generator[EufRecord, None, None]:
        for record in importer.parse():
            if self._check_euf_record(record, importer, context):
                yield record

    def _do_lift_over(
        self,
        importer: EufImporter,
        context: _ReadOnlyImportContext | _DatasetImportContext,
    ) -> Generator[EufRecord, None, None]:
        def generator():
            for record in importer.parse():
                if self._check_euf_record(record, importer, context):
                    yield record

        assembly = self._assembly_service.get_by_id(context.assembly_id)
        current_assembly_name = self._assembly_service.get_name_for_version(
            assembly.taxa_id
        )
        logger.info(
            f"Lifting over dataset from {assembly.name} to {current_assembly_name}..."
        )
        raw_file = self._bedtools_service.create_temp_euf_file(generator())
        with self._assembly_service.create_lifted_file(assembly, raw_file) as fp:
            lifted_importer = EufImporter(stream=fp, source=fp.name)
            for lifted_record in self._do_direct_import(lifted_importer, context):
                yield lifted_record


@cache
def get_validator_service() -> ValidatorService:
    """Instantiate a ValidatorService object by injecting its dependencies.

    :returns: Import service instance
    :rtype: ValidatorService
    """
    return ValidatorService(
        session=get_session(),
        annotation_service=get_annotation_service(),
        assembly_service=get_assembly_service(),
        bedtools_service=get_bedtools_service(),
    )

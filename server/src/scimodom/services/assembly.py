import json
import logging
from functools import cache
from typing import Sequence, TextIO

from requests.exceptions import HTTPError
from sqlalchemy import select, func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import Assembly, AssemblyVersion, Taxa
from scimodom.services.ensembl import (
    EnsemblAssemblyClient,
    get_ensembl_assembly_client,
)
from scimodom.services.external import get_external_service, ExternalService
from scimodom.services.file import FileService, get_file_service
from scimodom.services.web import WebService, get_web_service
from scimodom.utils.utils import gen_short_uuid
from scimodom.utils.specs.enums import (
    AssemblyFileType,
    Identifiers,
    ImportLimits,
)

logger = logging.getLogger(__name__)


class AssemblyNotFoundError(Exception):
    """Exception for handling a non-existing Assembly."""

    pass


class AssemblyVersionError(Exception):
    """Exception for handling an Assembly version mismatch."""

    pass


class AssemblyAbortedError(Exception):
    """Exception for handling assembly creation.

    Handle general errors associated with adding or
    creating assemblies e.g. request streaming, etc.
    """

    pass


class LiftOverError(Exception):
    """Exception for handling errors in liftover."""

    pass


class AssemblyService:
    """Utility class to manage assemblies.

    This service orchestrates the database, the file system, and
    the downloads. Everything specific to Ensembl is delegated
    to EnsemblAssemblyClient.

    :param session: SQLAlchemy ORM session
    :param external_service: External service instance
    :param web_service: The web service
    :param file_service: The file service
    :param ensembl_client: Client for Ensembl, created from
    'web_service' if not given.
    """

    def __init__(
        self,
        session: Session,
        external_service: ExternalService,
        web_service: WebService,
        file_service: FileService,
        ensembl_client: EnsemblAssemblyClient,
    ) -> None:
        self._session = session
        self._external_service = external_service
        self._web_service = web_service
        self._file_service = file_service
        self._ensembl_client = ensembl_client

    @property
    def _version(self) -> str:
        """Current assembly (database) version.

        This is read from the database on each access (not cached).
        The file and the assembly services always agree,
        even if the version changes while the process is running.
        """
        return self._session.execute(select(AssemblyVersion.version_num)).scalar_one()

    def get_by_id(self, assembly_id: int) -> Assembly:
        """Retrieve assembly by ID.

        :param assembly_id: Assembly ID
        :raises NoResultFound: If no such assembly.
        :return: Assembly
        """
        return self._session.get_one(Assembly, assembly_id)

    def get_by_taxa_and_name(self, taxa_id: int, assembly_name: str) -> Assembly:
        """Retrieve assembly by taxa ID and name.

        :param taxa_id: Taxonomy ID
        :param assembly_name: Assembly name
        :raises NoResultFound: If no such assembly.
        :return: Assembly
        """
        return self._session.execute(
            select(Assembly).filter_by(taxa_id=taxa_id, name=assembly_name)
        ).scalar_one()

    def get_assemblies_by_taxa(self, taxa_id: int) -> Sequence[Assembly]:
        """Retrieve all assemblies for a given organism.

        :param taxa_id: Taxonomy ID
        :return: list of Assembly instances
        """
        return (
            self._session.execute(select(Assembly).filter_by(taxa_id=taxa_id))
            .scalars()
            .all()
        )

    def is_latest_assembly(self, assembly: Assembly) -> bool:
        """Check if assembly version matches latest version.

        :param assembly: Assembly instance
        :return: True if assembly version is
        the same as database version, else False
        """
        return assembly.version == self._version

    def get_name_for_version(self, taxa_id: int) -> str:
        """Get assembly name for latest version.

        :param taxa_id: Taxonomy ID
        :raises NoResultFound: If no assembly for the latest version.
        :return: Assembly name
        """
        return self._session.execute(
            select(Assembly.name).filter_by(taxa_id=taxa_id, version=self._version)
        ).scalar_one()

    def get_chroms(self, taxa_id: int) -> list[dict[str, str | int]]:
        """Return chrom.sizes for the latest database version.

        :param taxa_id: Taxonomy ID
        :return: chrom names and sizes
        """
        chroms = []
        with self._file_service.open_assembly_file(
            taxa_id, AssemblyFileType.CHROM
        ) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                chrom, size = line.split(None, 1)
                chroms.append({"chrom": chrom, "size": int(size.strip())})
        return chroms

    def create_lifted_file(
        self,
        assembly: Assembly,
        raw_file: str,
        unmapped_file: str | None = None,
        threshold: float = ImportLimits.LIFTOVER.max,
    ) -> TextIO:
        """Liftover records to current assembly.

        :param assembly: Assembly instance
        :param raw_file: BED file to be lifted over
        :param unmapped_file: Unmapped features
        :param threshold: Threshold for raising LiftOverError
        :return: File handle pointing to the liftedOver features
        """
        if self.is_latest_assembly(assembly):
            raise AssemblyVersionError("Cannot liftover for latest assembly.")

        chain_file = self._file_service.get_assembly_file_path(
            assembly.taxa_id,
            file_type=AssemblyFileType.CHAIN,
            assembly_name=assembly.name,
        )

        raw_lines = self._file_service.count_lines(raw_file)
        lifted_file, unmapped_file = self._external_service.get_crossmap_output(
            raw_file, chain_file.as_posix(), unmapped_file
        )

        unmapped_lines = self._file_service.count_lines(unmapped_file)
        unmapped_fraction = unmapped_lines / raw_lines if raw_lines > 0 else 0.0
        if unmapped_fraction > threshold:
            raise LiftOverError(
                f"Liftover failed: {unmapped_lines} unmapped records out of {raw_lines}"
            )
        if unmapped_lines > 0:
            logger.warning(f"Liftover: {unmapped_lines} unmapped records.")
        return self._file_service.open_file_for_reading(lifted_file)

    def add_assembly(self, taxa_id: int, assembly_name: str) -> None:
        """Add an assembly to the database if it does not exist.

        Create the directory structure, and add the corresponding
        files. The current assembly must already exist in the database,
        but `assembly_name` may or may not exist; if it does, nothing
        is done. Integrity is checked by asking both the file system
        for the expected directory structure and the database for a
        matching record.

        :param taxa_id: Taxa ID
        :param assembly_name: A valid assembly name.
        :raises NoResultFound: If a required assembly is missing.
        :raises AssemblyNotFoundError: If 'assembly_name' is not valid.
        """
        if self._file_service.check_if_assembly_exists(taxa_id, assembly_name):
            try:
                self.get_by_taxa_and_name(taxa_id, assembly_name)
                return
            except NoResultFound as exc:
                exc.add_note(
                    f"Orphaned files detected: '{assembly_name}' has files on "
                    "the system but no database record"
                )
                raise

        try:
            current_assembly_name = self.get_name_for_version(taxa_id)
        except NoResultFound as exc:
            exc.add_note(
                "No database record for current assembly: "
                f"Cannot add '{assembly_name}'"
            )
            raise
        if assembly_name == current_assembly_name:
            assembly = self.get_by_taxa_and_name(taxa_id, assembly_name)
            self.create_current(assembly)
            return

        valid_assembly_names = self.get_coord_system_versions(taxa_id)
        if assembly_name not in valid_assembly_names:
            raise AssemblyNotFoundError(
                f"'{assembly_name}' for organism '{taxa_id}' not found. "
                f"Valid assemblies are: '{' '.join(valid_assembly_names)}'"
            )
        self._create_version(taxa_id, assembly_name)

    def create_current(self, assembly: Assembly) -> None:
        """Create directory and files for the current assembly version.

        :param assembly: Current assembly
        :raises AssemblyVersionError: If not current version.
        :raises AssemblyAbortedError: If fail to create files.
        """
        if not self.is_latest_assembly(assembly):
            raise AssemblyVersionError(
                f"Version mismatch for '{assembly.name}': "
                f"Version is '{assembly.version}', "
                f"but database provides '{self._version}'"
            )

        if self._file_service.check_if_assembly_exists(
            assembly.taxa_id,
            assembly.name,
        ):
            return

        logger.info(f"Setting up assembly '{assembly.name}' for current version...")

        try:
            self._handle_gene_build(assembly)
            self._handle_release(assembly)
            self._handle_dna_sequences(assembly)
        except AssemblyVersionError:
            self._discard_assembly_files(assembly.taxa_id, assembly.name)
            raise
        except Exception as exc:
            self._discard_assembly_files(assembly.taxa_id, assembly.name)
            raise AssemblyAbortedError(
                f"Aborted: Could not create system files for '{assembly.name}'"
            ) from exc

    def get_coord_system_versions(self, taxa_id: int) -> list[str]:
        """Retrieve valid assemblies for a given taxon.

        :param taxa_id: Taxonomy ID
        :return: Valid assembly names
        """
        with self._file_service.open_assembly_file(
            taxa_id, AssemblyFileType.INFO
        ) as fp:
            info = json.load(fp)
        return info["coord_system_versions"]

    def _create_version(self, taxa_id: int, assembly_name: str) -> None:
        logger.info(f"Setting up a new assembly for '{assembly_name}'...")
        try:
            url = self._ensembl_client.get_chain_file_url(
                self._get_organism(taxa_id),
                assembly_name,
                self.get_name_for_version(taxa_id),
            )
            with self._file_service.create_chain_file(taxa_id, assembly_name) as fh:
                self._web_service.stream_request_to_file(url, fh)
            self._add_assembly_record_if_missing(taxa_id, assembly_name)
        except Exception as exc:
            self._session.rollback()
            self._discard_assembly_files(taxa_id, assembly_name)
            raise AssemblyAbortedError(
                f"Aborted: Could not add '{assembly_name}'"
            ) from exc

    def _add_assembly_record_if_missing(self, taxa_id: int, assembly_name: str) -> None:
        try:
            self.get_by_taxa_and_name(taxa_id, assembly_name)
        except NoResultFound:
            version_nums = (
                self._session.execute(select(func.distinct(Assembly.version)))
                .scalars()
                .all()
            )
            version_num = gen_short_uuid(Identifiers.ASSEMBLY.length, version_nums)
            assembly = Assembly(
                name=assembly_name, taxa_id=taxa_id, version=version_num
            )
            self._session.add(assembly)
            self._session.commit()

    def _discard_assembly_files(self, taxa_id: int, assembly_name: str) -> None:
        # system clean-up must never raise not to loose the original error
        try:
            self._file_service.delete_assembly(taxa_id, assembly_name)
        except FileNotFoundError:
            # nothing was created before the failure
            pass
        except Exception:
            logger.warning(
                f"Failed to remove files for assembly '{assembly_name}'. "
                "Check the file system!",
                exc_info=True,
            )

    def _get_seqids(self, taxa_id: int) -> list[str]:
        return [d["chrom"] for d in self.get_chroms(taxa_id)]

    def _get_organism(self, taxa_id: int) -> str:
        return self._session.execute(
            select(Taxa.name).filter_by(id=taxa_id)
        ).scalar_one()

    def _handle_release(self, assembly: Assembly):
        release = self._ensembl_client.get_data_release()
        with self._file_service.create_assembly_file(
            assembly.taxa_id, AssemblyFileType.RELEASE
        ) as fp:
            json.dump(release, fp, indent="\t")

    def _handle_gene_build(self, assembly: Assembly):
        gene_build = self._ensembl_client.get_gene_build(
            self._get_organism(assembly.taxa_id)
        )
        coord_sysver = self._ensembl_client.get_coord_system_version(gene_build)
        if coord_sysver != assembly.name:
            raise AssemblyVersionError(
                f"Version mismatch for '{assembly.name}': "
                f"coord system version provides '{coord_sysver}'"
            )
        chroms, top_level = self._ensembl_client.get_top_level_regions(gene_build)
        with self._file_service.create_assembly_file(
            assembly.taxa_id, AssemblyFileType.CHROM
        ) as fh:
            for chrom in sorted(chroms):
                fh.write(f"{chrom}\t{top_level[chrom]}\n")

        with self._file_service.create_assembly_file(
            assembly.taxa_id, AssemblyFileType.INFO
        ) as fh:
            json.dump(
                self._ensembl_client.get_assembly_info(gene_build), fh, indent="\t"
            )

    def _handle_dna_sequences(self, assembly: Assembly):
        organism = self._get_organism(assembly.taxa_id)
        for chrom in self._get_seqids(assembly.taxa_id):
            self._download_dna_sequence(assembly, organism, chrom)
            self._file_service.index_dna_sequence_file(assembly.taxa_id, chrom)

    def _download_dna_sequence(
        self, assembly: Assembly, organism: str, chrom: str
    ) -> None:
        # fall back from "chromosome" to "primary_assembly" only on a 404
        urls = self._ensembl_client.get_dna_sequence_urls(
            organism, assembly.name, chrom
        )
        for idx, url in enumerate(urls):
            try:
                with self._file_service.create_dna_sequence_file(
                    assembly.taxa_id, chrom
                ) as fh:
                    self._web_service.stream_request_to_file(url, fh)
                return
            except HTTPError as exc:
                is_last = idx == len(urls) - 1
                if is_last or not _is_not_found(exc):
                    raise


def _is_not_found(exc: HTTPError) -> bool:
    response = getattr(exc, "response", None)
    return response is not None and response.status_code == 404


@cache
def get_assembly_service() -> AssemblyService:
    """Instantiate an AssemblyService object by injecting its dependencies.

    :return: Assembly service instance
    """
    return AssemblyService(
        session=get_session(),
        external_service=get_external_service(),
        web_service=get_web_service(),
        file_service=get_file_service(),
        ensembl_client=get_ensembl_assembly_client(),
    )

import json
import logging
from functools import cache
from posixpath import join as urljoin
from typing import Any, Sequence, TextIO

from requests.exceptions import HTTPError
from sqlalchemy import select, func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import Assembly, AssemblyVersion, Taxa
from scimodom.services.external import get_external_service, ExternalService
from scimodom.services.file import FileService, get_file_service
from scimodom.services.web import WebService, get_web_service
from scimodom.utils.utils import gen_short_uuid
from scimodom.utils.specs.enums import (
    AssemblyFileType,
    Identifiers,
    Ensembl,
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

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param external_service: External service instance
    :type external service: ExternalService
    :param web_service: The web service
    :type web_service: WebService
    :param file_service: The file service
    :type file_service: FileService
    """

    def __init__(
        self,
        session: Session,
        external_service: ExternalService,
        web_service: WebService,
        file_service: FileService,
    ) -> None:
        self._session = session
        self._external_service = external_service
        self._web_service = web_service
        self._file_service = file_service

        self._version = self._session.execute(
            select(AssemblyVersion.version_num)
        ).scalar_one()

    def get_by_id(self, assembly_id: int) -> Assembly:
        """Retrieve assembly by ID.

        :param assembly_id: Assembly ID
        :type assembly_id: int
        :return: Assembly
        :rtype: Assembly
        """
        return self._session.get_one(Assembly, assembly_id)

    def get_by_taxa_and_name(self, taxa_id: int, assembly_name: str) -> Assembly:
        """Retrieve assembly by taxa ID and name.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :param assembly_name: Assembly name
        :type assembly_name: str
        :returns: Assembly
        :rtype: Assembly
        """
        return self._session.execute(
            select(Assembly).filter_by(taxa_id=taxa_id, name=assembly_name)
        ).scalar_one()

    def get_assemblies_by_taxa(self, taxa_id: int) -> Sequence[Assembly]:
        """Retrieve all assemblies for a given organism.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: lsit of Assembly instances
        :rtype: list of Assembly
        """
        return (
            self._session.execute(select(Assembly).filter_by(taxa_id=taxa_id))
            .scalars()
            .all()
        )

    def is_latest_assembly(self, assembly: Assembly) -> bool:
        """Check if assembly version matches latest version.

        :param assembly: Assembly instance
        :type assembly: Assembly
        :returns: True if assembly version is
        the same as database version, else False
        :rtype: bool
        """
        return assembly.version == self._version

    def get_name_for_version(self, taxa_id: int) -> str:
        """Get assembly name for latest version.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: Assembly name
        :rtype: str
        """
        return self._session.execute(
            select(Assembly.name).filter_by(taxa_id=taxa_id, version=self._version)
        ).scalar_one()

    def get_seqids(self, taxa_id: int) -> list[str]:
        """Return chromosomes for a given assembly as a list.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: Chromosomes
        :rtype: list of str
        """
        with self._file_service.open_assembly_file(
            taxa_id, AssemblyFileType.CHROM
        ) as fp:
            lines = fp.readlines()
        return [line.split()[0] for line in lines]

    def get_chroms(self, taxa_id: int) -> list[dict[str, Any]]:
        """Return chrom.sizes for the latest database version.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: chrom names and sizes
        :rtype: list[dict[str, Any]]
        """

        def _yield_chroms():
            with self._file_service.open_assembly_file(
                taxa_id, AssemblyFileType.CHROM
            ) as fh:
                for line in fh:
                    chrom, size = line.strip().split(None, 1)
                    yield {"chrom": chrom, "size": int(size.strip())}

        return list(_yield_chroms())

    def create_lifted_file(
        self,
        assembly: Assembly,
        raw_file: str,
        unmapped_file: str | None = None,
        threshold: float = ImportLimits.LIFTOVER.max,
    ) -> TextIO:
        """Liftover records to current assembly.

        :param assembly: Assembly instance
        :type assembly: Assembly
        :param raw_file: BED file to be lifted over
        :type raw_file: str
        :param unmapped_file: Unmapped features
        :type unmapped_file: str | None
        :param threshold: Threshold for raising LiftOverError
        :type threshold: float
        :returns: File handle pointing to the liftedOver features
        :rtype: TextIO
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
        if unmapped_lines / raw_lines > threshold:
            raise LiftOverError(
                f"Liftover failed: {unmapped_lines} records out of {raw_lines} could not be mapped."
            )
        if unmapped_lines > 0:
            logger.warning(
                f"{unmapped_lines} records could not be mapped... "
                "Contact the system administrator if you have questions."
            )
        return self._file_service.open_file_for_reading(lifted_file)

    def add_assembly(self, taxa_id: int, assembly_name: str) -> None:
        """Add an assembly to the database if it does not exist.

        Create the directory structure, and add the corresponding
        files.

        The current assembly must exist in the database, but
        any other assembly may or may not exist. No other assumptions
        are made on the caller: the assembly is created if it does
        not exist, but the state of the database must be consistent
        with the content of the file system for the given assembly.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param assembly_name: A valid assembly name. If the
        assembly already exists, nothing is done.
        :type assembly_name: str
        :raises NoResultFound: If a required assembly is missing.
        :raises AssemblyNotFoundError: If 'assembly_name' is not valid.
        """
        if self._file_service.check_if_assembly_exists(taxa_id, assembly_name):
            try:
                self.get_by_taxa_and_name(taxa_id, assembly_name)
                return
            except NoResultFound as exc:
                msg = f"Files exists for '{assembly_name}', but assembly is missing."
                exc.add_note(msg)
                raise

        try:
            current_assembly_name = self.get_name_for_version(taxa_id)
            if assembly_name == current_assembly_name:
                assembly = self.get_by_taxa_and_name(taxa_id, assembly_name)
                self.create_current(assembly)
                return
        except NoResultFound as exc:
            msg = f"Cannot add '{assembly_name}' if current assembly is missing."
            exc.add_note(msg)
            raise

        valid_assembly_names = self.get_coord_system_versions(taxa_id)
        if assembly_name not in valid_assembly_names:
            raise AssemblyNotFoundError(
                f"No such assembly '{assembly_name}' for organism '{taxa_id}'. "
                f"Valid assemblies are: '{' '.join(valid_assembly_names)}'"
            )
        self._create_version(taxa_id, assembly_name)

    def create_current(self, assembly: Assembly) -> None:
        """Create directory and files for the current assembly version.

        :param assembly: Current assembly
        :type assembly: Assembly
        :raises AssemblyVersionError: If not current version.
        :raises AssemblyAbortedError: If fail to create files.
        :raises Exception: Unhandled exceptions
        """
        if not self.is_latest_assembly(assembly):
            raise AssemblyVersionError(
                f"Mismatch between assembly version '{assembly.version}' and "
                f"database version '{self._version}'."
            )

        if self._file_service.check_if_assembly_exists(assembly.taxa_id, assembly.name):
            return

        logger.info(f"Setting up assembly {assembly.name} for current version...")

        try:
            self._handle_gene_build(assembly)
            self._handle_release(assembly)
            self._handle_dna_sequences(assembly)
        except AssemblyVersionError:
            self._file_service.delete_assembly(assembly.taxa_id, assembly.name)
            raise
        except Exception as exc:
            self._file_service.delete_assembly(assembly.taxa_id, assembly.name)
            raise AssemblyAbortedError(
                f"Adding assembly for ID '{assembly.id}' aborted."
            ) from exc

    def get_coord_system_versions(self, taxa_id: int) -> list[str]:
        """Retrieve valid assemblies for a given taxa ID.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :return: Valid assembly names
        :rtype: list[str]
        """
        with self._file_service.open_assembly_file(
            taxa_id, AssemblyFileType.INFO
        ) as fp:
            info = json.load(fp)
        return info["coord_system_versions"]

    def _create_version(self, taxa_id: int, assembly_name: str) -> None:
        logger.info(f"Setting up a new assembly for {assembly_name}...")
        try:
            url = self._get_ensembl_chain_file_url(taxa_id, assembly_name)
            with self._file_service.create_chain_file(taxa_id, assembly_name) as fh:
                self._web_service.stream_request_to_file(url, fh)
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
        except Exception as exc:
            self._session.rollback()
            self._file_service.delete_assembly(taxa_id, assembly_name)
            raise AssemblyAbortedError(
                f"Adding assembly for '{assembly_name}' aborted."
            ) from exc

    def _get_ensembl_chain_file_url(self, taxa_id: int, assembly_name: str):
        chain_file_name = AssemblyFileType.CHAIN.value(
            source_assembly=assembly_name,
            target_assembly=self.get_name_for_version(taxa_id),
        )
        return urljoin(
            Ensembl.FTP.value,
            Ensembl.ASM_MAPPING.value,
            self._get_organism_for_ensembl_url(taxa_id),
            chain_file_name,
        )

    def _get_ensembl_dna_sequence_url(
        self, taxa_id: int, assembly_name: str, chrom: str, is_alt: bool = False
    ):
        organism = self._get_organism_for_ensembl_url(taxa_id)
        seq_file_name = AssemblyFileType.DNA.value(
            organism=organism.capitalize(), assembly=assembly_name, chrom=chrom
        )
        if is_alt:
            seq_file_name = AssemblyFileType.get_alt_name(seq_file_name)

        return urljoin(
            Ensembl.FTP.value,
            Ensembl.FASTA.value,
            organism,
            "dna",
            seq_file_name,
        )

    def _get_organism_for_ensembl_url(self, taxa_id: int):
        organism = self._get_organism(taxa_id)
        return ("_".join(organism.split())).lower()

    def _get_ensembl_gene_build_url(self, taxa_id: int):
        return urljoin(
            Ensembl.REST.value,
            Ensembl.ASM.value,
            self._get_organism_for_ensembl_url(taxa_id),
        )

    def _get_organism(self, taxa_id: int) -> str:
        organism = self._session.execute(
            select(Taxa.name).filter_by(id=taxa_id)
        ).scalar_one()
        return organism

    def _handle_release(self, assembly: Assembly):
        url = urljoin(
            Ensembl.REST.value,
            Ensembl.DATA.value,
        )
        release = self._web_service.request_as_json(url)
        with self._file_service.create_assembly_file(
            assembly.taxa_id, AssemblyFileType.RELEASE
        ) as fp:
            json.dump(release, fp, indent="\t")

    def _handle_gene_build(self, assembly: Assembly):
        url = self._get_ensembl_gene_build_url(assembly.taxa_id)
        gene_build = self._web_service.request_as_json(url)
        coord_sysver = gene_build["default_coord_system_version"]
        if coord_sysver != assembly.name:
            raise AssemblyVersionError(
                f"Mismatch between assembly {assembly.name} and coord system "
                f"version {coord_sysver}."
            )
        chroms = gene_build["karyotype"]
        top_level = {
            d["name"]: d["length"]
            for d in gene_build["top_level_region"]
            if d["coord_system"] in ["chromosome", "primary_assembly"]
            and d["name"] in chroms
        }
        with self._file_service.create_assembly_file(
            assembly.taxa_id, AssemblyFileType.CHROM
        ) as fh:
            for chrom in sorted(chroms):
                fh.write(f"{chrom}\t{top_level[chrom]}\n")

        keys = [
            "assembly_accession",
            "assembly_date",
            "assembly_name",
            "coord_system_versions",
        ]
        gene_build = {k: v for k, v in gene_build.items() if k in keys}
        with self._file_service.create_assembly_file(
            assembly.taxa_id, AssemblyFileType.INFO
        ) as fh:
            json.dump(gene_build, fh, indent="\t")

    def _handle_dna_sequences(self, assembly: Assembly):
        chroms = self.get_seqids(assembly.taxa_id)
        for chrom in chroms:
            url = self._get_ensembl_dna_sequence_url(
                assembly.taxa_id, assembly.name, chrom
            )
            try:
                with self._file_service.create_dna_sequence_file(
                    assembly.taxa_id, chrom
                ) as fh:
                    self._web_service.stream_request_to_file(url, fh)
            except HTTPError:
                # chromosome -> primary_assembly
                url = self._get_ensembl_dna_sequence_url(
                    assembly.taxa_id, assembly.name, chrom, is_alt=True
                )
                with self._file_service.create_dna_sequence_file(
                    assembly.taxa_id, chrom
                ) as fh:
                    self._web_service.stream_request_to_file(url, fh)
            self._file_service.index_dna_sequence_file(assembly.taxa_id, chrom)


@cache
def get_assembly_service() -> AssemblyService:
    """Instantiate an AssemblyService object by injecting its dependencies.

    :returns: Assembly service instance
    :rtype: AssemblyService
    """
    return AssemblyService(
        session=get_session(),
        external_service=get_external_service(),
        web_service=get_web_service(),
        file_service=get_file_service(),
    )

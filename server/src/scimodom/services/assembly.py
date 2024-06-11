import json
import logging
from pathlib import Path
from posixpath import join as urljoin
import shutil
from typing import ClassVar, Callable, Any

import requests  # type: ignore
from sqlalchemy.orm import Session
from sqlalchemy import select, exists, func

from scimodom.config import Config
from scimodom.database.models import Assembly, Taxa
import scimodom.database.queries as queries
from scimodom.utils.operations import liftover_to_file
import scimodom.utils.specifications as specs
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)


class InstantiationError(Exception):
    """Exception handling for AssemblyService instantiation."""

    pass


class AssemblyVersionError(Exception):
    """Exception handling for Assembly version mismatch."""

    pass


class LiftOverError(Exception):
    """Exception for handling too many
    unmapped records during liftover."""

    pass


class AssemblyService:
    """Utility class to manage assemblies.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param assembly_id: Assembly ID
    :type assembly_id: int
    :param name: Assembly name
    :type name: str
    :param taxa_id: Taxa ID
    :type taxa_id: int
    :param ASSEMBLY_NUM_LENGTH: Length of assembly ID
    :type ASSEMBLY_NUM_LENGTH: int
    :param DATA_PATH: Path to assembly
    :type DATA_PATH: str | Path | None
    :param DATA_SUB_PATH: Subpath to assembly
    :type DATA_SUB_PATH: str
    :param CHROM_fILE: File name with a list of
    allowed chromosomes
    :type CHROM_FILE: str
    :param CHAIN_FILE: Chain file template name
    :type CHAIN_FILE: str
    """

    ASSEMBLY_NUM_LENGTH: ClassVar[int] = specs.ASSEMBLY_NUM_LENGTH
    DATA_PATH: ClassVar[str | Path] = Config.DATA_PATH
    DATA_SUB_PATH: ClassVar[str] = "assembly"
    CHROM_FILE: ClassVar[str] = "chrom.sizes"
    CHAIN_FILE: ClassVar[Callable] = "{source}_to_{target}.chain.gz".format

    def __init__(self, session: Session, **kwargs) -> None:
        """Initializer method."""
        self._session = session

        self._assembly_id: int
        self._db_version: str
        self._name: str
        self._taxid: int
        self._chrom_file: Path

        # current DB assembly version
        query = queries.get_assembly_version()
        self._db_version = self._session.execute(query).scalar_one()

        assembly_id = kwargs.get("assembly_id", None)
        if assembly_id is not None:
            is_found = self._session.query(
                exists().where(Assembly.id == assembly_id)
            ).scalar()
            if not is_found:
                msg = f"Assembly ID = {assembly_id} not found! Aborting transaction!"
                raise InstantiationError(msg)
            self._assembly_id = assembly_id
            query = queries.query_column_where(
                Assembly,
                ["version", "name", "taxa_id"],
                filters={"id": self._assembly_id},
            )
            records = self._session.execute(query).one()
            version = records[0]
            # forbid instantiation for "other" assembly versions
            if not version == self._db_version:
                msg = (
                    f"Mismatch between current DB assembly version ({self._db_version}) and "
                    f"version ({version}) from assembly ID = {self._assembly_id}. Aborting transaction!"
                )
                raise AssemblyVersionError(msg)
            self._name = records[1]
            self._taxid = records[2]
        else:
            self._name = kwargs.get("name", None)
            self._taxid = kwargs.get("taxa_id", None)
            if not isinstance(self._name, str):
                raise TypeError(f"Expected str; got {type(self._name).__name__}")
            # difficult to validate "name", or combination of (name, taxa_id)
            # because "name" can be a "new" assembly...
            is_found = self._session.query(
                exists().where(Taxa.id == self._taxid)
            ).scalar()
            if not is_found:
                msg = f"Taxonomy ID = {self._taxid} not found! Aborting transaction!"
                raise InstantiationError(msg)
            query = queries.query_column_where(
                Assembly, "id", filters={"name": self._name, "taxa_id": self._taxid}
            )
            assembly_id = self._session.execute(query).scalar_one_or_none()
            if assembly_id:
                # can be any version, if not current database version
                # there may be limitations to what can be done
                self._assembly_id = assembly_id
            else:
                # download chain files for "new" assembly
                try:
                    self._new()
                    self._session.commit()  # add "new" assembly ID
                except:
                    self._session.rollback()
                    raise

        # chrom file for the current DB assembly version
        self._set_chrom_path()

    def __new__(cls, session: Session, **kwargs):
        """Constructor method."""
        if cls.DATA_PATH is None:
            msg = "Missing environment variable: DATA_PATH. Terminating!"
            raise ValueError(msg)
        elif not Path(cls.DATA_PATH, cls.DATA_SUB_PATH).is_dir():
            msg = f"DATA PATH {Path(cls.DATA_PATH, cls.DATA_SUB_PATH)} not found! Terminating!"
            raise FileNotFoundError(msg)
        else:
            return super(AssemblyService, cls).__new__(cls)

    @classmethod
    def from_id(cls, session: Session, assembly_id: int):
        """Provides AssemblyService factory when ID is known.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param assembly_id: Assembly ID
        :type assembly_id: int
        :returns: AssemblyService class instance
        :rtype: AssemblyService
        """
        service = cls(session, assembly_id=assembly_id)
        return service

    @classmethod
    def from_new(cls, session: Session, name: str, taxa_id: int):
        """Provides AssemblyService factory when ID is unknown, i.e.
        only name and organism are provided. Calls _new() if assembly
        is missing.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param name: Assembly name
        :type name: str
        :param taxa_id: Assembly taxa_id
        :type taxa_id: int
        :returns: AssemblyService class instance
        :rtype: AssemblyService
        """
        service = cls(session, name=name, taxa_id=taxa_id)
        return service

    @staticmethod
    def get_assembly_path() -> Path:
        """Construct parent path to assembly files.

        :returns: Path to assembly
        :rtype: Path
        """
        return Path(AssemblyService.DATA_PATH, AssemblyService.DATA_SUB_PATH)

    @staticmethod
    def get_chrom_path(organism: str, assembly: str) -> tuple[Path, str]:
        """Construct file path (chrom sizes) for a
        given organism and assemly. Since there is only
        one file per organism, for the current Assembly
        version, assembly must also match the current
        Assembly, but this method cannot check this.
        This method attempts to format organism.

        :param organism: Organism name
        :type organism: str
        :param assembly: Assembly name
        :type assembly: str
        :returns: Parent and file name
        :rtype: tuple[str | Path, str]
        """
        organism = "_".join(organism.lower().split()).capitalize()
        path = AssemblyService.get_assembly_path()
        parent = Path(path, organism, assembly)
        return parent, AssemblyService.CHROM_FILE

    @staticmethod
    def get_seqids(
        organism: str | None = None,
        assembly: str | None = None,
        chrom_file: str | Path | None = None,
    ) -> list[str]:
        """Returns the chromosomes for a given assembly
        as a list. Relies on get_chrom_path, as such
        assembly must also match the current assembly.

        :param organism: Organism name
        :type organism: str | None
        :param assembly: Assembly name
        :type assembly: str | None
        :param chrom_file: Path to chrom.sizes
        :type chrom_file: str | Path | None
        :returns: Chromosomes
        :rtype: list of str
        """
        if chrom_file is None:
            parent, filen = AssemblyService.get_chrom_path(organism, assembly)
            chrom_file = Path(parent, filen)
        with open(chrom_file, "r") as f:
            lines = f.readlines()
        return [l.split()[0] for l in lines]

    def get_chain_path(self) -> tuple[Path, str]:
        """Construct file path (chain file) for organism.
        Only to (not from) current version.

        :returns: Parent and file name
        :rtype: tuple[str | Path, str]
        """
        organism = self._get_organism()
        parent = Path(self.get_assembly_path(), organism, self._name)
        # assembly_id may not be the current assembly version
        name = self._get_current_name()
        filen = self.CHAIN_FILE(source=self._name, target=name)
        return parent, filen

    def create_new(self):
        """Creates a new assembly for current DB version, mostly for
        maintenance/initial setup. Does not upgrade DB version."""

        msg = "Setting directories up for new assembly for current version..."
        logger.info(msg)

        query = queries.query_column_where(
            Assembly, "version", filters={"id": self._assembly_id}
        )
        version = self._session.execute(query).scalar_one()
        if not version == self._db_version:
            msg = (
                f"Mismatch between current DB assembly version ({self._db_version}) and "
                f"version ({version}). Cannot call this function! Aborting transaction!"
            )
            raise AssemblyVersionError(msg)

        self._set_chrom_path()
        parent = self._chrom_file.parent
        try:
            parent.mkdir(parents=True, exist_ok=False)
        except FileExistsError as error:
            msg = f"Assembly directory at {parent} already exists... Aborting transaction!"
            raise Exception(msg) from error

        msg = "Downloading assembly info..."
        logger.info(msg)

        url = urljoin(
            specs.ENSEMBL_SERVER,
            specs.ENSEMBL_ASM,
            self._get_organism().lower(),
        )
        request = requests.get(url, headers={"Content-Type": "application/json"})
        if not request.ok:
            shutil.rmtree(parent)
            request.raise_for_status()
        gene_build = request.json()
        coord_sysver = gene_build["default_coord_system_version"]
        if not coord_sysver == self._name:
            msg = (
                f"Mismatch between assembly {self._name} and current coord system "
                f"version {coord_sysver}. Upgrade your database! Aborting transaction!"
            )
            shutil.rmtree(parent)
            raise AssemblyVersionError(msg)

        chroms = gene_build["karyotype"]
        top_level = {
            d["name"]: d["length"]
            for d in gene_build["top_level_region"]
            if d["coord_system"] == "chromosome" and d["name"] in chroms
        }
        with open(self._chrom_file, "x") as cfile:
            for chrom in sorted(chroms):
                cfile.write(f"{chrom}\t{top_level[chrom]}\n")

        keys = ["assembly_accession", "assembly_date", "assembly_name"]
        gene_build = {k: v for k, v in gene_build.items() if k in keys}
        with open(Path(parent, "info.json"), "w") as f:
            json.dump(gene_build, f, indent="\t")

        url = urljoin(
            specs.ENSEMBL_SERVER,
            specs.ENSEMBL_DATA,
        )
        request = requests.get(url, headers={"Content-Type": "application/json"})
        if not request.ok:
            shutil.rmtree(parent)
            request.raise_for_status()
        release = request.json()
        with open(Path(parent, "release.json"), "w") as f:
            json.dump(release, f, indent="\t")

    def liftover(self, records: list[tuple[Any, ...]], threshold: float = 0.3) -> str:
        """Liftover records to current assembly.
        Unmapped features are discarded.

        :param records: Records to be lifted over
        :type records: List of tuple of (str, ...) - Data records
        :param threshold: Threshold for raising LiftOverError
        :type threshold: float
        :returns: Files pointing to the liftedOver features
        :rtype: str
        """
        parent, filen = self.get_chain_path()
        chain_file = Path(parent, filen).as_posix()
        lifted_file, unmapped_file = liftover_to_file(records, chain_file)

        def _count_lines(reader):
            b = reader(1024 * 1024)
            while b:
                yield b
                b = reader(1024 * 1024)

        with open(unmapped_file, "rb") as fh:
            unmapped_lines = sum(
                line.count(b"\n") for line in _count_lines(fh.raw.read)
            )
        failed_liftover = unmapped_lines / len(records) > threshold
        if failed_liftover:
            raise LiftOverError
        msg = (
            f"{unmapped_lines} records could not be mapped and were discarded... "
            "Contact the system administrator if you have questions."
        )
        logger.warning(msg)

        return lifted_file

    def _get_current_name(self) -> str:
        """Get current assembly name. This methods
        allows to get the assembly name for the current
        database version, i.e. not necessarily the
        name for the class instance, which could be for
        a different version."""
        query = queries.query_column_where(
            "Assembly",
            "name",
            filters={"taxa_id": self._taxid, "version": self._db_version},
        )
        return self._session.execute(query).scalar_one()

    def _get_organism(self):
        """Query organism from taxonomy ID"""
        query = queries.query_column_where(
            "Taxa",
            "name",
            filters={"id": self._taxid},
        )
        organism = self._session.execute(query).scalar_one()
        organism = "_".join(organism.split())
        return organism

    def _set_chrom_path(self) -> None:
        """Assign chrom file path. This is the same
        irrespective of assembly version, i.e. there
        is only one chrom file for the current version."""
        organism = self._get_organism()
        name = self._get_current_name()
        parent, filen = self.get_chrom_path(organism, name)
        self._chrom_file = Path(parent, filen)

    def _new(self):
        """Prepares a "new" assembly. This assembly is new in the
        sense that it does not yet exists, but is not necessarily
        a newer assembly version. This method essentially downloads
        the chain file (from assembly to current database version).
        To create an assembly for the current database assembly
        version, see create_new().
        """

        msg = "Setting directories up for a new assembly..."
        logger.info(msg)

        parent, filen = self.get_chain_path()
        chain_file = Path(parent, filen)
        organism = self._get_organism()
        try:
            parent.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            msg = (
                f"Assembly directory at {parent} already exists despite calling AssemblyService "
                "from new... Aborting transaction!"
            )
            raise Exception(msg) from exc

        msg = "Downloading chain files..."
        logger.info(msg)

        url = urljoin(
            specs.ENSEMBL_FTP, specs.ENSEMBL_ASM_MAPPING, organism.lower(), filen
        )
        with requests.get(url, stream=True) as request:
            if not request.ok:
                shutil.rmtree(parent)
                request.raise_for_status()
            with open(chain_file, "wb") as f:
                for chunk in request.iter_content(chunk_size=10 * 1024):
                    f.write(chunk)

        query = select(func.distinct(Assembly.version))
        version_nums = self._session.execute(query).scalars().all()
        version_num = utils.gen_short_uuid(self.ASSEMBLY_NUM_LENGTH, version_nums)
        assembly = Assembly(name=self._name, taxa_id=self._taxid, version=version_num)
        self._session.add(assembly)
        self._session.flush()
        self._assembly_id = assembly.id

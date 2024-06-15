import json
import logging
from pathlib import Path
from posixpath import join as urljoin
import shutil
from typing import ClassVar, Callable, Any

import requests  # type: ignore
from sqlalchemy.orm import Session
from sqlalchemy import select, exists, func
from sqlalchemy.exc import NoResultFound

from scimodom.config import Config
from scimodom.database.models import Assembly, AssemblyVersion, Taxa
from scimodom.services.external import get_external_service
from scimodom.utils.specifications import (
    ASSEMBLY_NUM_LENGTH,
    ENSEMBL_FTP,
    ENSEMBL_SERVER,
    ENSEMBL_DATA,
    ENSEMBL_ASM,
    ENSEMBL_ASM_MAPPING,
)
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)


class AssemblyNotFoundError(Exception):
    """Exception handling for a non-existing Assembly."""

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
    :param DATA_PATH: Data path
    :type DATA_PATH: str | Path | None
    :param ASSEMBLY_PATH: Path to assembly
    :type ASSEMBLY_PATH: str
    :param CHROM_fILE: Reserved file name with a
    list of allowed chromosomes
    :type CHROM_FILE: str
    :param CHAIN_FILE: Chain file template name
    :type CHAIN_FILE: Callable
    """

    DATA_PATH: ClassVar[str | Path] = Config.DATA_PATH
    ASSEMBLY_PATH: ClassVar[str] = "assembly"
    CHROM_FILE: ClassVar[str] = "chrom.sizes"
    CHAIN_FILE: ClassVar[Callable] = "{source}_to_{target}.chain.gz".format

    def __init__(self, session: Session) -> None:
        self._session = session

        self._version = self._session.execute(
            select(AssemblyVersion.version_num)
        ).scalar_one()

    def __new__(cls, session: Session):
        if cls.DATA_PATH is None:
            msg = "Missing environment variable: DATA_PATH."
            raise ValueError(msg)
        elif not Path(cls.DATA_PATH, cls.ASSEMBLY_PATH).is_dir():
            msg = f"DATA PATH {Path(cls.DATA_PATH, cls.ASSEMBLY_PATH)} not found!"
            raise FileNotFoundError(msg)
        else:
            return super().__new__(cls)

    @staticmethod
    def get_assembly_path() -> Path:
        """Construct parent path to assembly files.

        :returns: Path to assembly
        :rtype: Path
        """
        return Path(AssemblyService.DATA_PATH, AssemblyService.ASSEMBLY_PATH)

    def get_chrom_file(self, taxa_id: int) -> Path:
        """Construct file path (chrom sizes) for a
        given organism.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: Path to chrom.sizes
        :rtype: Path
        """
        path, organism, name_for_version = self._path_constructor(taxa_id)
        return Path(path, organism, name_for_version, self.CHROM_FILE)

    def get_chain_file(self, taxa_id: int, name: str) -> Path:
        """Construct file path (chain file) for organism.
        Only to (not from) current version.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :param name: Assembly name
        :type name: str
        :returns: Path to chain file
        :rtype: Path
        """
        path, organism, name_for_version = self._path_constructor(taxa_id)
        chain_file = self.CHAIN_FILE(source=name, target=name_for_version)
        return Path(path, organism, name, chain_file)

    def get_assembly_by_id(self, assembly_id: int) -> Assembly:
        """Retrieve assembly.

        :param assembly_id: Assembly ID
        :type assembly_id: int
        :returns: Assembly instance
        :rtype: Assembly

        :raises: AssemblyNotFoundError
        """
        try:
            return self._session.get_one(Assembly, assembly_id)
        except NoResultFound:
            raise AssemblyNotFoundError(f"No such assembly with ID: {assembly_id}.")

    def is_latest_assembly(self, assembly: Assembly) -> bool:
        """Check if assembly version matches the
        database latest version.

        :param assembly: Assembly instance
        :type assembly: Assembly
        :returns: True if assembly version is
        the same as databas version, else False
        :rtype: bool
        """
        return assembly.version == self._version

    def get_seqids(self, taxa_id: int) -> list[str]:
        """Returns the chromosomes for a given assembly
        as a list.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: Chromosomes
        :rtype: list of str
        """
        chrom_file = self.get_chrom_file(taxa_id)
        with open(chrom_file, "r") as f:
            lines = f.readlines()
        return [l.split()[0] for l in lines]

    def liftover(
        self, assembly: Assembly, raw_file: str, threshold: float = 0.3
    ) -> str:
        """Liftover records to current assembly.
        Unmapped features are discarded.

        :param assembly: Assembly instance
        :type assembly: Assembly
        :param raw_file: BED file to be lifted over
        :type records: str
        :param threshold: Threshold for raising LiftOverError
        :type threshold: float
        :returns: Files pointing to the liftedOver features
        :rtype: str
        """
        if self.is_latest_assembly(assembly):
            raise AssemblyVersionError("Cannot liftover for latest assembly.")
        chain_file = self.get_chain_file(assembly.taxa_id, assembly.name)
        if not chain_file.is_file():
            raise FileNotFoundError(f"No such file or directory {chain_file}.")

        raw_lines = self._count_lines(raw_file)
        external_service = get_external_service()
        lifted_file, unmapped_file = external_service.get_crossmap_output(
            raw_file, chain_file.as_posix()
        )

        unmapped_lines = self._count_lines(unmapped_file)
        if unmapped_lines / raw_lines > threshold:
            raise LiftOverError(
                f"Liftover failed: {unmapped_lines} records of {raw_lines} could not be mapped."
            )
        if unmapped_lines > 0:
            logger.warning(
                f"{unmapped_lines} records could not be mapped and were discarded... "
                "Contact the system administrator if you have questions."
            )
        return lifted_file

    def add_assembly(self, taxa_id: int, name: int) -> None:
        """Add a new assembly to the database if it does
        not exist.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :param name: Assembly name
        :type name: str
        """
        try:
            self._session.execute(
                select(Assembly).filter_by(taxa_id=taxa_id, name=name)
            ).scalar_one()
            return
        except NoResultFound:
            pass

        chain_file = self.get_chain_file(taxa_id, name)
        organism = self._get_organism(taxa_id)
        try:
            chain_file.parent.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise Exception(
                f"Assembly does not exist, but file exists: {chain_file.parent}."
            ) from exc

        logger.info(f"Setting up a new assembly for {name}...")

        url = urljoin(
            ENSEMBL_FTP, ENSEMBL_ASM_MAPPING, organism.lower(), chain_file.name
        )
        with requests.get(url, stream=True) as request:
            if not request.ok:
                shutil.rmtree(chain_file.parent)
                request.raise_for_status()
            with open(chain_file, "wb") as f:
                for chunk in request.iter_content(chunk_size=10 * 1024):
                    f.write(chunk)

        version_nums = (
            self._session.execute(select(func.distinct(Assembly.version)))
            .scalars()
            .all()
        )
        version_num = utils.gen_short_uuid(ASSEMBLY_NUM_LENGTH, version_nums)
        assembly = Assembly(name=name, taxa_id=taxa_id, version=version_num)
        self._session.add(assembly)
        self._session.commit()

    def prepare_assembly_for_version(self, assembly_id: int) -> None:
        """Setup directories and files for the current database assembly version.
        The assembly must exists in the database. This is mostly for initial setup.
        This method does not upgrade the database version.

        :param assembly_id: Assembly ID
        :type assembly_id: int
        """
        assembly = self.get_assembly_by_id(assembly_id)
        if not self.is_latest_assembly(assembly):
            raise AssemblyVersionError(
                f"Mismatch between assembly version {assembly.version} and database version {self._version}."
            )

        logger.info(f"Setting up assembly {assembly.name} for current version...")

        chrom_file = self.get_chrom_file(assembly.taxa_id)
        parent = chrom_file.parent
        try:
            parent.mkdir(parents=True, exist_ok=False)
        except FileExistsError as error:
            msg = f"Assembly directory exists: {parent}."
            raise Exception(msg) from error

        try:
            self._handle_gene_build(assembly, chrom_file)
            self._handle_release(parent)
        except:
            shutil.rmtree(parent)
            raise

        # assembly_id = kwargs.get("assembly_id", None)
        # if assembly_id is not None:
        #     is_found = self._session.query(
        #         exists().where(Assembly.id == assembly_id)
        #     ).scalar()
        #     if not is_found:
        #         msg = f"Assembly ID = {assembly_id} not found! Aborting transaction!"
        #         raise InstantiationError(msg)
        #     self._assembly_id = assembly_id
        #     query = queries.query_column_where(
        #         Assembly,
        #         ["version", "name", "taxa_id"],
        #         filters={"id": self._assembly_id},
        #     )
        #     records = self._session.execute(query).one()
        #     version = records[0]
        #     # forbid instantiation for "other" assembly versions
        #     if not version == self._db_version:
        #         msg = (
        #             f"Mismatch between current DB assembly version ({self._db_version}) and "
        #             f"version ({version}) from assembly ID = {self._assembly_id}. Aborting transaction!"
        #         )
        #         raise AssemblyVersionError(msg)
        #     self._name = records[1]
        #     self._taxid = records[2]
        # else:
        #     self._name = kwargs.get("name", None)
        #     self._taxid = kwargs.get("taxa_id", None)
        #     if not isinstance(self._name, str):
        #         raise TypeError(f"Expected str; got {type(self._name).__name__}")
        #     # difficult to validate "name", or combination of (name, taxa_id)
        #     # because "name" can be a "new" assembly...
        #     is_found = self._session.query(
        #         exists().where(Taxa.id == self._taxid)
        #     ).scalar()
        #     if not is_found:
        #         msg = f"Taxonomy ID = {self._taxid} not found! Aborting transaction!"
        #         raise InstantiationError(msg)
        #     query = queries.query_column_where(
        #         Assembly, "id", filters={"name": self._name, "taxa_id": self._taxid}
        #     )
        #     assembly_id = self._session.execute(query).scalar_one_or_none()
        #     if assembly_id:
        #         # can be any version, if not current database version
        #         # there may be limitations to what can be done
        #         self._assembly_id = assembly_id
        #     else:
        #         # download chain files for "new" assembly
        #         try:
        #             self._new()
        #             self._session.commit()  # add "new" assembly ID
        #         except:
        #             self._session.rollback()
        #             raise

        # # chrom file for the current DB assembly version
        # self._set_chrom_path()

    @staticmethod
    def _count_lines(path):
        count = 0
        with open(path) as fp:
            while True:
                buffer = fp.read(1024 * 1024)
                if len(buffer) == 0:
                    return count
                count += buffer.count("\n")

    @staticmethod
    def _request_as_json(url):
        request = requests.get(url, headers={"Content-Type": "application/json"})
        if not request.ok:
            request.raise_for_status()
        return request.json()

    @staticmethod
    def _handle_release(path):
        url = urljoin(
            ENSEMBL_SERVER,
            ENSEMBL_DATA,
        )
        release = AssemblyService._request_as_json(url)
        with open(Path(path, "release.json"), "w") as f:
            json.dump(release, f, indent="\t")

    def _handle_gene_build(self, assembly: Assembly, chrom_file):
        url = urljoin(
            ENSEMBL_SERVER,
            ENSEMBL_ASM,
            self._get_organism(assembly.taxa_id).lower(),
        )
        gene_build = self._request_as_json(url)
        coord_sysver = gene_build["default_coord_system_version"]
        if coord_sysver != assembly.name:
            raise AssemblyVersionError(
                f"Mismatch between assembly {assembly.name} and coord system version "
                f"{coord_sysver}. Upgrade your database!"
            )
        chroms = gene_build["karyotype"]
        top_level = {
            d["name"]: d["length"]
            for d in gene_build["top_level_region"]
            if d["coord_system"] == "chromosome" and d["name"] in chroms
        }
        with open(chrom_file, "x") as cfile:
            for chrom in sorted(chroms):
                cfile.write(f"{chrom}\t{top_level[chrom]}\n")

        keys = ["assembly_accession", "assembly_date", "assembly_name"]
        gene_build = {k: v for k, v in gene_build.items() if k in keys}
        with open(Path(chrom_file.parent, "info.json"), "w") as f:
            json.dump(gene_build, f, indent="\t")

    def _get_organism(self, taxa_id: int) -> str:
        organism = self._session.execute(
            select(Taxa.name).filter_by(id=taxa_id)
        ).scalar_one()
        organism = "_".join(organism.split())
        return organism

    def _get_name_for_version(self, taxa_id: int) -> str:
        name = self._session.execute(
            select(Assembly.name).filter_by(taxa_id=taxa_id, version=self._version)
        ).scalar_one()
        return name

    def _path_constructor(self, taxa_id: int) -> tuple[Path, str, str]:
        path = self.get_assembly_path()
        organism = self._get_organims(taxa_id)
        name_for_version = self._get_name_for_version(taxa_id)
        return path, organism, name_for_version

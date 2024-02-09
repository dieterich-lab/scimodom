#! /usr/bin/env python3

import json
import logging
from pathlib import Path
from posixpath import join as urljoin
from typing import ClassVar

import requests  # type: ignore
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from scimodom.config import Config
from scimodom.database.models import Assembly, Taxa
import scimodom.database.queries as queries
import scimodom.utils.specifications as specs
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)


class AssemblyVersionError(Exception):
    """Exception handling for Assembly version mismatch."""

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
    """

    ASSEMBLY_NUM_LENGTH: ClassVar[int] = specs.ASSEMBLY_NUM_LENGTH
    DATA_PATH: ClassVar[str | Path] = Config.DATA_PATH
    DATA_SUB_PATH: ClassVar[str] = "assembly"

    def __init__(self, session: Session, **kwargs) -> None:
        """Initializer method."""
        self._session = session
        self._is_new: bool = False

        self._assembly_id: int
        self._db_version: str
        self._name: str
        self._taxid: int
        self._chrom_file: Path

        query = queries.get_assembly_version()
        self._db_version = self._session.execute(query).scalar()

        assembly_id = kwargs.get("assembly_id", None)
        if assembly_id is not None:
            self._assembly_id = assembly_id
            query = queries.query_column_where(
                Assembly,
                ["name", "taxa_id", "version"],
                filters={"id": self._assembly_id},
            )
            records = [r._asdict() for r in self._session.execute(query)][0]
            version = records["version"]
            # forbid instantiation for "other" assembly versions
            if not version == self._db_version:
                msg = (
                    f"Mismatch between current DB assembly version ({self._db_version}) and "
                    f"version ({version}) from assembly ID = {self._assembly_id}. Aborting transaction!"
                )
                raise AssemblyVersionError(msg)
            self._name = records["name"]
            self._taxid = records["taxa_id"]
            self._set_chrom_path()
        else:
            self._name = kwargs.get("name", None)
            self._taxid = kwargs.get("taxa_id", None)
            if not isinstance(self._name, str):
                raise TypeError(f"Expected str; got {type(self._name).__name__}")
            if not isinstance(self._taxid, int):
                raise TypeError(f"Expected int; got {type(self._taxid).__name__}")
            # difficult to validate name, or combination of (name, taxa_id)...
            # use select(func.dictinct(Organism.taxa_id)) for available IDs
            query = select(Taxa.id)
            if self._taxid not in session.execute(query).scalars().all():
                msg = f"Taxonomy ID = {self._taxid} not found! Aborting transaction!"
                raise ValueError(msg)
            query = queries.query_column_where(
                Assembly, "id", filters={"name": self._name, "taxa_id": self._taxid}
            )
            assembly_id = self._session.execute(query).scalar_one_or_none()
            if assembly_id:
                self._assembly_id = assembly_id
                self._set_chrom_path()
            else:
                query = select(func.distinct(Assembly.version))
                version_nums = self._session.execute(query).scalars().all()
                version_num = utils.gen_short_uuid(
                    self.ASSEMBLY_NUM_LENGTH, version_nums
                )
                assembly = Assembly(
                    name=self._name, taxa_id=self._taxid, version=version_num
                )
                self._session.add(assembly)
                self._session.commit()
                self._assembly_id = assembly.id
                self._is_new = True

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
        :param id: Assembly ID
        :type id: int
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
        :type name: int
        :returns: AssemblyService class instance
        :rtype: AssemblyService
        """
        service = cls(session, name=name, taxa_id=taxa_id)
        if service._is_new:
            msg = "Calling new assembly..."
            logger.debug(msg)
            service._new()
        return service

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

    def get_chain_path(self) -> tuple[Path, str]:
        """Construct file path (chain file) for organism.
        Only to (not from) current version.

        :returns: Parent and file name
        :rtype: tuple[str | Path, str]
        """
        organism = self._get_organism()
        parent = Path(self.DATA_PATH, self.DATA_SUB_PATH, organism, self._name)
        # assembly_id may not be the current assembly version
        query = queries.query_column_where(
            "Assembly",
            "name",
            filters={"taxa_id": self._taxid, "version": self._db_version},
        )
        name = self._session.execute(query).scalar_one()
        filen = f"{self._name}_to_{name}.chain.gz"
        return parent, filen

    @staticmethod
    def get_chrom_path(
        path: str | Path | None, organism: str, assembly: str
    ) -> tuple[Path, str]:
        """Construct file path (chrom sizes) for organism

        :param path: Base path
        :type path: str | Path
        :param organism: Organism
        :type organism: str
        :param assembly: Assembly
        :type assembly: str
        :returns: Parent and file name
        :rtype: tuple[str | Path, str]
        """
        if path is None:
            raise TypeError("Missing DATA PATH! Cannot construct path to chrom.sizes!")
        parent = Path(path, organism, assembly)
        return parent, "chrom.sizes"

    def _set_chrom_path(self, path: bool = False) -> Path | None:
        """Assign chrom.size path

        :param path: Return parent path or not
        :type path: bool
        :returns: parent
        :rtype: Path
        """
        organism = self._get_organism()
        parent, filen = self.get_chrom_path(
            Path(self.DATA_PATH, self.DATA_SUB_PATH), organism, self._name
        )
        self._chrom_file = Path(parent, filen)
        if path:
            return parent
        else:
            return None

    def _new(self):
        """Prepare new assembly, i.e. get chain files, but this
        does not create an assembly for the current DB assembly version,
        see create_new().
        """

        msg = "Setting directories up for new assembly..."
        logger.debug(msg)

        parent = self._set_chrom_path(path=True)
        try:
            parent.mkdir(parents=True, exist_ok=False)
        except FileExistsError as error:
            msg = (
                f"Assembly directory at {parent} already exists despite calling AssemblyService "
                "from new... Aborting transaction!"
            )
            raise Exception(msg) from error

        msg = "Downloading chain files..."
        logger.debug(msg)

        organism = self._get_organism()
        parent, filen = self.get_chain_path()
        chain_file = Path(parent, filen)

        url = urljoin(
            specs.ENSEMBL_FTP, specs.ENSEMBL_ASM_MAPPING, organism.lower(), filen
        )
        with requests.get(url, stream=True) as request:
            if not request.ok:
                request.raise_for_status()
            try:
                with open(chain_file, "wb") as f:
                    for chunk in request.iter_content(chunk_size=10 * 1024):
                        f.write(chunk)
            except FileExistsError:
                msg = f"File at {chain_file} exists. Skipping!"
                logger.warning(msg)

    def create_new(self):
        """Creates a new assembly for current DB version, mostly for
        maintenance/initial setup."""

        msg = "Setting directories up for new assembly for current version..."
        logger.debug(msg)

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

        parent = self._set_chrom_path(path=True)
        try:
            parent.mkdir(parents=True, exist_ok=False)
        except FileExistsError as error:
            msg = f"Assembly directory at {parent} already exists... Aborting transaction!"
            raise Exception(msg) from error

        msg = "Downloading assembly info..."
        logger.debug(msg)

        url = urljoin(
            specs.ENSEMBL_SERVER,
            specs.ENSEMBL_ASM,
            self._get_organism().lower(),
        )
        request = requests.get(url, headers={"Content-Type": "application/json"})
        if not request.ok:
            request.raise_for_status()
        gene_build = request.json()
        coord_sysver = gene_build["default_coord_system_version"]
        if not coord_sysver == self._name:
            msg = (
                f"Mismatch between assembly {self._name} and current coord system "
                f"version {coord_sysver}. Upgrade your database! Aborting transaction!"
            )
            raise AssemblyVersionError(msg)

        chroms = gene_build["karyotype"]
        top_level = {
            d["name"]: d["length"]
            for d in gene_build["top_level_region"]
            if d["coord_system"] == "chromosome" and d["name"] in chroms
        }
        try:
            with open(self._chrom_file, "x") as cfile:
                for chrom in sorted(chroms):
                    cfile.write(f"{chrom}\t{top_level[chrom]}\n")
        except FileExistsError:
            # this shoud not happen as we checked for directory above...
            msg = f"File at {self._chrom_file} exists. Skipping!"
            logger.warning(msg)

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
            request.raise_for_status()
        release = request.json()
        with open(Path(parent, "release.json"), "w") as f:
            json.dump(release, f, indent="\t")

from pathlib import Path
from typing import TextIO, Iterable, ClassVar, Any

from sqlalchemy.orm import Session

from scimodom.database.database import Base
from scimodom.database.models import Data
from scimodom.services.importer.base import BaseImporter
import scimodom.utils.specifications as specs
import scimodom.utils.utils as utils


class SpecsError(Exception):
    """Exception handling for specification errors."""

    pass


class EUFDataImporter(BaseImporter):
    """Utility class to import bedRMod (EU) formatted files.
    This class only handles the actual records, not the header,
    cf. EUFHeaderImporter.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param filen: File path
    :type filen: str
    :param handle: File handle
    :type handle: TextIO
    :param association: A dictionary of association IDs of the form
    {name: association_id}, where name is the modification short_name.
    The association ID provides information about the dataset (EUFID),
    the modification, the organism, and the technology used.
    :type association: dict of {str: int}
    :param seqids: List of chromosomes or scaffolds. The seqid must be
    one used with Ensembl, e.g. standard Ensembl chromosome name w/o
    the "chr" prefix. Only records with seqid in seqids will be imported.
    :type seqids: list of str
    :param SPECS: Default specs
    :type SPECS: dict
    """

    SPECS: ClassVar[dict] = specs.SPECS_EUF

    def __init__(
        self,
        session: Session,
        filen: str,
        handle: TextIO,
        association: dict[str, int],
        seqids: list[str],
    ) -> None:
        """Initializer method."""
        # self._sep: str = self.SPECS["delimiter"]
        # self._htag: str = self.SPECS["header"]["comment"]
        # self._hsep: str = self.SPECS["header"]["delimiter"]
        # self._hrequired: list[str]
        # self._version: str | None = None
        # self._specs: dict
        # self._int_types: list

        self._model: Base = Data
        self._dtypes: dict[str, dict[str, Any]] = dict()

        self._session = session
        self._filen = filen
        self._handle = handle
        self._association = association
        self._seqids = seqids

    def parse_record(self, record: dict[str, str]) -> dict[str, Any]:
        pass

    def _cast_types(self) -> None:
        """Validate attributes and cast column types for input."""
        # assume order of __table__.columns is consistent...
        mapped_columns = utils.get_table_columns(self._model)
        mapped_types = utils.get_table_column_python_types(self._model)
        _dtypes = dict()
        for c in self._header:
            if c not in mapped_columns:
                msg = (
                    f"Column name {c} doesn't match any of the ORM mapped attribute names "
                    f"for {self._model.__name__}. This is likely due to a change in model declaration."
                )
                raise Exception(msg)
            idx = mapped_columns.index(c)
            _dtypes[c] = mapped_types[idx]
        self._dtypes[self._model.__name__] = _dtypes

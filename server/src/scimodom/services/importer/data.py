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
    :param specs_ver: Version of EUF specs to use
    :type specs_ver: str
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
        specs_ver: str,
    ) -> None:
        """Initializer method."""

        # TODO: lift or not no_flush

        self._session = session
        self._filen = filen
        self._handle = handle
        self._association = association
        self._seqids = seqids
        self._specs_ver = specs_ver

        self._model: Base = Data
        self._sep: str = self.SPECS["delimiter"]
        self._comment: str = self.SPECS["header"]["comment"]
        self._constraints: dict[str, str | list[str]] = self.SPECS["constraints"]
        self._specs: dict[str, dict[str, str] | list[str]] = self.SPECS[self._specs_ver]

        self._dtypes: dict[str, Any]
        self._itypes: list[str]

        self._cast_types()

        super().__init__(
            session=session,
            filen=filen,
            handle=handle,
            model=self._model,
            header=self._specs["columns"].values(),
            sep=self._sep,
            comment=self._comment,
        )

    def parse_record(self, record: dict[str, str]) -> dict[str, Any]:
        """Data parser.

        :param record: A data record (line) as a dictionary
        :type record: dict of {str: str}
        :return: A data record as a dictionary, with value
        typecasted to that required by the model. A record can
        contain additonal entries for the model table columns.
        :rtype: dict of {str: Any}
        """

        # cast to float numerical types, to avoid ValueError for
        # non "integer-like" input records. NOTE: data loss may occur!
        frecord = {k: float(v) if k in self._itypes else v for k, v in record.items()}
        crecord = {k: self._dtypes[k].__call__(v) for k, v in frecord.items()}
        # validate record
        for itype in self._itypes:
            if crecord[itype] < 0:
                raise ValueError(f"Value {itype}: {crecord['itype']} out of range.")
        if crecord["chrom"] not in self._seqids:
            raise ValueError(
                f"Unrecognized chrom: {crecord['chrom']}. Ignore this warning"
                "for scaffolds and contigs, otherwise this could be due to misformatting!"
            )
        if crecord["strand"] not in self._constraints["strand"]:
            raise ValueError(f"Unrecognized strand: {crecord['strand']}.")
        for c in ["score", "frequency"]:
            if not eval(self._constraints[c], {}, {c: crecord[c]}):
                raise ValueError(f"Value score: {crecord[c]} out of range.")
        # add missing columns for model table
        try:
            crecord["association_id"] = self._association[crecord["name"]]
        except:
            raise ValueError(f"Unrecognized name: {crecord['name']}.")

        return crecord

    def _cast_types(self) -> None:
        """Cast column types for input."""
        # order of __table__.columns always the same...?
        mapped_columns = utils.get_table_columns(self._model)
        mapped_types = utils.get_table_column_python_types(self._model)
        self._dtypes = {
            c: mapped_types[mapped_columns.index(c)] for c in mapped_columns
        }
        self._itypes = [
            k
            for k, v in self._dtypes.items()
            if k in self._specs["columns"].values() and v.__name__ == "int"
        ]

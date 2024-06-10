from pathlib import Path
from typing import Union

from scimodom.database.database import get_session
from scimodom.services.importer.base import BaseImporter
from scimodom.services.importer.data import EUFDataImporter
from scimodom.services.importer.generic import BEDImporter
from scimodom.services.importer.header import EUFHeaderImporter


class Importer:
    """Defines a general Importer class to handle
    EU (bedRMod) formatted files.

    :param header: EU header importer
    :type header: EUFHeaderImporter
    :param data: EU data importer
    :type data: EUFDataImporter
    """

    def __init__(
        self,
        header: EUFHeaderImporter,
        data: EUFDataImporter | None = None,
    ) -> None:
        """Initializer method."""
        self.header = header
        self.data = data

        self._association: dict[str, int]
        self._seqids: list[str]
        self._version: str
        self._eufid: str

    def init_data_importer(
        self, association: dict[str, int], seqids: list[str], **kwargs
    ) -> None:
        """Instantiate EUFDataImporter unless it already exists.

        :param association: A dictionary of the form {short_name: modification_id},
        where short_name is the modification short_name.
        :type association: dict of {str: int}
        :param seqids: List of chromosomes or scaffolds. The seqid must be
        one used with Ensembl, e.g. standard Ensembl chromosome name w/o
        the "chr" prefix. Only records with seqid in seqids will be imported.
        :type seqids: list of str
        """

        self._association = association
        self._seqids = seqids
        self._version = self.header._specs_ver
        self._eufid = self.header._eufid

        filen = self.header._filen
        session = get_session()
        if self.header._handle.closed is False:
            self.header.close()
        if self.data is None:
            self.data = EUFDataImporter(
                session=session(),
                filen=filen,
                handle=open(filen, "r"),
                eufid=self._eufid,
                association=self._association,
                seqids=self._seqids,
                specs_ver=self._version,
                **kwargs,
            )

    def reset_data_importer(self, filen: str, **kwargs) -> None:
        """Reset EUFDataImporter. This method is intended to be used
        after a liftOver.

        :param filen: File path to liftedOver features
        :type association: str
        """
        session = get_session()
        self.data = EUFDataImporter(
            session=session(),
            filen=filen,
            handle=open(filen, "r"),
            eufid=self._eufid,
            association=self._association,
            seqids=self._seqids,
            specs_ver=self._version,
            **kwargs,
        )


def get_importer(
    filen: str, smid: str, eufid: str, title: str, organism_id: int, technology_id: int
):
    """Instantiate Importer.

    :param filen: File path
    :type filen: str
    :param smid: Sci-ModoM project ID or SMID
    :type smid: str
    :param eufid: EUF ID (dataset) or EUFID
    :type eufid: str
    :param title: Title associated with EUF/bedRMod dataset
    :type title: str
    :param organism_id: Organism ID
    :type organism_id: int
    :param technology_id: Technology ID
    :type technology_id: int
    """
    session = get_session()

    return Importer(
        header=EUFHeaderImporter(
            session=session(),
            filen=filen,
            handle=open(filen, "r"),
            smid=smid,
            eufid=eufid,
            title=title,
            organism_id=organism_id,
            technology_id=technology_id,
        ),
        data=None,
    )


def get_bed_importer(filen: Union[str, Path], **kwargs):
    """Instantiate BED Importer.

    :param filen: File path
    :type filen: str
    """
    session = get_session()

    return BEDImporter(
        session=session(), filen=filen, handle=open(filen, "r"), **kwargs
    )


def get_buffer(model, no_flush: bool = False):
    """Returns a buffer to import data.
    There is no commit method implemented, this
    must be called separately. There is no check
    on the data.

    :param model: SQLAlchemy model
    :type model: Base
    :param no_flush: Data is flushed by default,
    otherwise there is no flush on calling "buffer_data".
    This does not affect calls to "flush"
    :type no_flush: bool
    """
    session = get_session()
    return BaseImporter._Buffer(session=session(), model=model, no_flush=no_flush)

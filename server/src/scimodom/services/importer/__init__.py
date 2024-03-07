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

    def init_data_importer(
        self, association: dict[str, int], seqids: list[str], **kwargs
    ) -> None:
        """Instantiate EUFDataImporter.

        :param association: A dictionary of association IDs of the form
        {name: association_id}, where name is the modification short_name.
        The association ID provides information about the dataset (EUFID),
        the modification, the organism, and the technology used.
        :type association: dict of {str: int}
        :param seqids: List of chromosomes or scaffolds. The seqid must be
        one used with Ensembl, e.g. standard Ensembl chromosome name w/o
        the "chr" prefix. Only records with seqid in seqids will be imported.
        :type seqids: list of str
        """

        self._association = association
        self._seqids = seqids
        self._version = self.header._specs_ver

        filen = self.header._filen
        session = get_session()
        if self.header._handle.closed is False:
            self.header.close()
        if self.data is None:
            self.data = EUFDataImporter(
                session=session(),
                filen=filen,
                handle=open(filen, "r"),
                association=self._association,
                seqids=self._seqids,
                specs_ver=self._version,
                **kwargs,
            )

    def reset_data_importer(self, filen: str, **kwargs) -> None:
        """Reset EUFDataImporter. This method is intended to be used
        after a liftOver. In this case, "name" is actually the
        "association_id".

        :param filen: File path to liftedOver features
        :type association: str
        """
        session = get_session()
        self.data = EUFDataImporter(
            session=session(),
            filen=filen,
            handle=open(filen, "r"),
            association=self._association,
            seqids=self._seqids,
            specs_ver=self._version,
            is_lifted=True,
            **kwargs,
        )


def get_importer(filen: str, smid: str, eufid: str, title: str):
    """Instantiate Importer.

    :param filen: File path
    :type filen: str
    :param smid: Sci-ModoM project ID or SMID
    :type smid: str
    :param eufid: EUF ID (dataset) or EUFID
    :type eufid: str
    :param title: Title associated with EUF/bedRMod dataset
    :type title: str
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
        ),
        data=None,
    )


def get_bed_importer(filen: str, **kwargs):
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

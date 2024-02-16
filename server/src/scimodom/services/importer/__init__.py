from scimodom.database.database import get_session
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

        version = self.header._specs_ver
        filen = self.header._filen
        session = get_session()
        if self.header._handle.closed is False:
            self.header.close()
        if self.data is None:
            self.data = EUFDataImporter(
                session=session(),
                filen=filen,
                handle=open(filen, "r"),
                association=association,
                seqids=seqids,
                specs_ver=version,
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

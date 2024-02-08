#! /usr/bin/env python3

import logging

logger = logging.getLogger(__name__)


class AssemblyService:
    """Utility class to manage assemblies.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param eufid: EUFID
    :type eufid: str
    :param taxid: Taxa ID
    :type taxid: int
    :param DATA_PATH: Path to annotation
    :type DATA_PATH: str | Path | None
    :param DATA_SUB_PATH: Subpath to annotation file
    :type DATA_SUB_PATH: str
    :param FMT: Annotation file format
    :type FMT: str
    """

    pass
    # DATA_PATH: ClassVar[str | Path] = Config.DATA_PATH
    # DATA_SUB_PATH: ClassVar[str] = "annotation"
    # FMT: ClassVar[str] = "gtf"  # 12.23 only handle GTF

    # def __init__(self, session: Session, **kwargs) -> None:
    #     """Initializer method."""
    #     self._session = session
    #     self._eufid: str
    #     self._taxa_id: int

    # TODO
    # 1. check if assembly exist (if it exists, check files, or assume all ok?), else add (lower version only...)
    # 2. if adding, download and prep files, incl. chain files (which ones, only from current DB version to lower?).

    # # assembly
    # # TODO: liftover (here or at data upload)
    # name = d_organism["assembly"]
    # query = queries.query_column_where(
    #     Assembly, "id", filters={"name": name, "taxa_id": taxa_id}
    # )
    # assembly_id = self._session.execute(query).scalar()
    # if not assembly_id:
    #     # add new version for new entry, presumably a lower assembly
    #     # that will not be used (i.e. data must be lifted)
    #     query = select(Assembly.version)
    #     version_nums = self._session.execute(query).scalars().all()
    #     version_num = utils.gen_short_uuid(
    #         self.ASSEMBLY_NUM_LENGTH, version_nums
    #     )
    #     assembly = Assembly(name=name, taxa_id=taxa_id, version=version_num)
    #     self._session.add(assembly)
    #     self._session.commit()

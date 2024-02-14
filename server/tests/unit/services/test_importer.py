from io import StringIO
from pathlib import Path

import pytest

# from sqlalchemy import select

# from scimodom.database.models import Data, Dataset
from scimodom.services.importer import get_importer

# import scimodom.utils.utils as utils


# test struture with rollback to checkpoint in case e.g. data or header is wrong
# test closing or not the open connection
# WHY WAS I ABLE TO ADD ASSOCIATION ID TO DATA IF THERE IS NO VALUE IN THE DB (FK)???

# we may have to write to a file here

# def test_

# get_importer(filen: str, smid: str, eufid: str, title: str)
# then call header methods

#     def init_data_importer(
#         self, association: dict[str, int], seqids: list[str]
# then call dataimporter methods
# check


#             also test BED either separately, or just here

# def get_bed_importer(
#     filen: str,

# do we need to test also e.g. short/long lines, no cols, etc.?


def test_importer(Session, data_path):
    importer = get_importer(
        filen=Path(data_path.LOC, "test.bed").as_posix(),
        smid="12345678",
        eufid="123456789ABC",
        title="title",
    )
    importer.header.parse_header()
    importer.header.close()

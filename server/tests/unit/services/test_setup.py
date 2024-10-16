from io import StringIO

import pytest

from scimodom.services.setup import SetupService

# one example table...
# cf. #30

TAXONOMY_CSV = """id,domain,kingdom,phylum,note
1,Eukarya,Animalia,Chordata,e.g. human or mouse
2,Eukarya,Animalia,Arthropoda,e.g. D. melanogaster
3,Eukarya,Animalia,Nematoda,e.g. C. elegans
4,Eukarya,Fungi,,e.g. S. cerevisiae
5,Eukarya,Plantae,,e.g. A. thaliana
6,Bacteria,,,e.g. E. coli
7,Vira,,,Not a domain (all viruses)"""


class MockFileService:
    @staticmethod
    def check_import_file(name):  # noqa
        return True

    @staticmethod
    def open_import_file(name):
        if name != "taxonomy.csv":
            raise FileNotFoundError()
        return StringIO(TAXONOMY_CSV)


def test_get_table(Session):
    setup = SetupService(Session(), file_service=MockFileService)  # noqa
    table = "taxonomy.csv"
    model = setup.FILE_NAME_TO_DB_TABLE_MAP[table]
    data = setup._get_import_file_as_dataframe(table)
    setup._validate_table(model, data)
    cols = data.columns.tolist()
    assert cols == ["id", "domain", "kingdom", "phylum"]

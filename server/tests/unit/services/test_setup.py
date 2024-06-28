from io import StringIO

import pytest

from scimodom.database.models import Taxonomy
from scimodom.services.setup import SetupService
import scimodom.utils.utils as utils

# one example table...

TAXONOMY_CSV = """id,domain,kingdom,phylum,note
1,Eukarya,Animalia,Chordata,e.g. human or mouse
2,Eukarya,Animalia,Arthropoda,e.g. D. melanogaster
3,Eukarya,Animalia,Nematoda,e.g. C. elegans
4,Eukarya,Fungi,,e.g. S. cerevisiae
5,Eukarya,Plantae,,e.g. A. thaliana
6,Bacteria,,,e.g. E. coli
7,Vira,,,Not a domain (all viruses)"""


# def test_bulk_upsert(Session):

# from sqlalchemy import select

# from scimodom.database.database import get_engine
# from scimodom.database.models import Taxonomy

# from scimodom.services.setup import SetupService

# setup = SetupService(Session())

# setup.validate_table(model, expected_table)

## FAILS -
##sqlalchemy.exc.UnsupportedCompilationError: Compiler <sqlalchemy.dialects.sqlite.base.SQLiteCompiler object at 0x7fd5937d1430> can't render element of type <class 'sqlalchemy.dialects.mysql.dml.OnDuplicateClause'> (Background on this error at: https://sqlalche.me/e/20/l7de)
# setup.bulk_upsert(model, expected_table)

# engine = get_engine()
# table = pd.read_sql_query(select(Taxonomy), engine)
##compare table and expected_table


class MockFileService:
    @staticmethod
    def check_import_file(name):
        return True
        # return name == 'taxonomy.csv'

    @staticmethod
    def open_import_file(name):
        if name != "taxonomy.csv":
            raise FileNotFoundError()
        return StringIO(TAXONOMY_CSV)


def test_get_table(Session):
    setup = SetupService(Session(), file_service=MockFileService)  # noqa

    expected_table = setup._get_import_file_as_dataframe("taxonomy.csv")
    cols = expected_table.columns.tolist()
    assert cols == ["id", "domain", "kingdom", "phylum"]

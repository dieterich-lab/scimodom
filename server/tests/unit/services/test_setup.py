from io import StringIO

import pytest
from sqlalchemy import UniqueConstraint

from scimodom.database.models import Annotation, AnnotationRelease
from scimodom.services.setup import SetupService

# cf. #30

TAXONOMY_CSV = """id,domain,kingdom,phylum,note
1,Eukarya,Animalia,Chordata,e.g. human or mouse
2,Eukarya,Animalia,Arthropoda,e.g. D. melanogaster
3,Eukarya,Animalia,Nematoda,e.g. C. elegans
4,Eukarya,Fungi,,e.g. S. cerevisiae
5,Eukarya,Plantae,,e.g. A. thaliana
6,Bacteria,,,e.g. E. coli
7,Vira,,,Not a domain (all viruses)"""

NCBI_TAXA_CSV = """id,name,short_name,taxonomy_id,note
9606,Homo sapiens,H. sapiens,007,human
10090,"Mus musculus",M. musculus,1,mouse"""


class MockFileService:
    @staticmethod
    def check_import_file(name):
        return True

    @staticmethod
    def open_import_file(name):
        valid_files = {
            "taxonomy.csv": TAXONOMY_CSV,
            "ncbi_taxa.csv": NCBI_TAXA_CSV,
        }
        if name not in valid_files:
            raise FileNotFoundError()
        return StringIO(valid_files[name])


class MockNcbiTaxaFileService:
    @staticmethod
    def open_import_file(name):
        return StringIO(NCBI_TAXA_CSV)


def test_get_table(Session):
    setup = SetupService(Session(), file_service=MockFileService)
    table = "taxonomy.csv"
    model = setup.FILE_NAME_TO_DB_TABLE_MAP[table]
    columns, records = setup._get_import_file_as_records(table)
    setup._validate_table(model, columns)
    assert columns == ["id", "domain", "kingdom", "phylum"]
    assert len(records) == 7
    assert records[0] == {
        "id": "1",
        "domain": "Eukarya",
        "kingdom": "Animalia",
        "phylum": "Chordata",
    }
    # empty values must be None, not float NaN
    assert records[3]["phylum"] is None
    values = [v for record in records for v in record.values()]
    assert not any(isinstance(v, float) for v in values)


def test_get_table_converts_integers(Session):
    setup = SetupService(Session(), file_service=MockFileService)
    _, records = setup._get_import_file_as_records("ncbi_taxa.csv")
    assert records == [
        {
            "id": 9606,
            "name": "Homo sapiens",
            "short_name": "H. sapiens",
            "taxonomy_id": "007",
        },
        {
            "id": 10090,
            "name": "Mus musculus",
            "short_name": "M. musculus",
            "taxonomy_id": "1",
        },
    ]


def test_validate_table_requires_more_than_one_column(Session):
    setup = SetupService(Session(), file_service=MockFileService)
    model = setup.FILE_NAME_TO_DB_TABLE_MAP["taxonomy.csv"]
    with pytest.raises(Exception, match="At least id"):
        setup._validate_table(model, ["id"])
    # these have a single column
    model = setup.FILE_NAME_TO_DB_TABLE_MAP["assembly_version.csv"]
    setup._validate_table(model, ["version_num"])


@pytest.mark.parametrize("content", ["", "other,columns\n1,2\n"])
def test_validate_table_no_columns(Session, content):
    setup = SetupService(Session(), file_service=MockFileService)
    setup._file_service = type(
        "FS", (), {"open_import_file": staticmethod(lambda name: StringIO(content))}
    )
    columns, _ = setup._get_import_file_as_records("taxonomy.csv")
    assert columns == []
    model = setup.FILE_NAME_TO_DB_TABLE_MAP["taxonomy.csv"]
    with pytest.raises(Exception, match="no valid columns"):
        setup._validate_table(model, columns)


def test_upsert_one_header_only_does_nothing(Session, mocker):
    setup = SetupService(Session(), file_service=MockFileService)
    setup._file_service = type(
        "FS",
        (),
        {"open_import_file": staticmethod(lambda name: StringIO("id,domain\n"))},
    )
    bulk = mocker.patch.object(setup, "_bulk_upsert")
    setup.upsert_one("taxonomy.csv")
    bulk.assert_not_called()


def test_import_order_satisfies_foreign_keys():
    # the order of FILE_NAME_TO_DB_TABLE_MAP is load-bearing: upsert_all
    # walks it, so a table must come after every table it references
    position = {
        model.__tablename__: i
        for i, model in enumerate(SetupService.FILE_NAME_TO_DB_TABLE_MAP.values())
    }
    for file_name, model in SetupService.FILE_NAME_TO_DB_TABLE_MAP.items():
        for foreign_key in model.__table__.foreign_keys:
            referred = foreign_key.column.table.name
            if referred == model.__tablename__ or referred not in position:
                continue
            assert position[referred] < position[model.__tablename__], (
                f"'{file_name}' references '{referred}', which must be "
                "imported before it"
            )


def test_annotation_release_archive_is_optional():
    # not every provider keeps a per-release archive; a null means
    # there is no release-specific page to link to. The archive is not
    # part of the key, so this does not weaken the foreign key from
    # Annotation, cf. AnnotationRelease
    assert AnnotationRelease.__table__.columns["archive"].nullable is True
    assert AnnotationRelease.__table__.columns["source"].nullable is False
    assert AnnotationRelease.__table__.columns["release"].nullable is False


def test_only_one_current_annotation_per_assembly_and_source():
    # the release is deliberately not part of the key: two releases of
    # the same source must not both be current on the same assembly
    uniques = {
        c.name: [col.name for col in c.columns]
        for c in Annotation.__table__.constraints
        if isinstance(c, UniqueConstraint)
    }
    assert uniques == {"uq_annotation_asv": ["assembly_id", "source", "version"]}

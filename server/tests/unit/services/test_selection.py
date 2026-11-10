from datetime import datetime
import pytest
from sqlalchemy import delete, func, select

from scimodom.database.models import (
    Dataset,
    DatasetModificationAssociation,
    DetectionTechnology,
    Modification,
    Organism,
    ProjectSelection,
    Selection,
)
from scimodom.services.selection import SelectionService
from scimodom.utils.dtos.project import (
    ProjectMetaDataDto,
    ProjectOrganismDto,
)


class MockGeneService:
    def __init__(self):
        self.deleted_cache_list: list[int] = []

    def delete_gene_cache(self, selection_id: int) -> None:
        self.deleted_cache_list.append(selection_id)


def _get_selection_service(Session):
    return SelectionService(Session(), gene_service=MockGeneService())


# tests


def _metadata(cto="Cell type 1", modomics_id="2000000006A", tech="Technology 1"):
    organism = ProjectOrganismDto(
        taxa_id=9606, cto=cto, assembly_name="GRCh38", assembly_id=1
    )
    return ProjectMetaDataDto(
        rna="WTS",
        modomics_id=modomics_id,
        tech=tech,
        method_id="91b145ea",
        organism=organism,
        note=None,
    )


def test_add_project_selections(Session, setup, project):  # noqa
    smid = project[0].id
    service = _get_selection_service(Session)
    service.add_project_selections(smid, [_metadata()])

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Modification)) == 1
        assert session.scalar(select(func.count()).select_from(Organism)) == 1
        assert (
            session.scalar(select(func.count()).select_from(DetectionTechnology)) == 1
        )
        project_selections = session.execute(select(ProjectSelection)).scalars().all()
        assert len(project_selections) == 1
        assert project_selections[0].project_id == smid
        assert project_selections[0].modification_id == 1
        assert project_selections[0].organism_id == 1
        assert project_selections[0].technology_id == 1
        # a selection exists only with data
        assert session.scalar(select(func.count()).select_from(Selection)) == 0


def test_add_project_selections_exist(Session, setup, project, caplog):  # noqa
    smid = project[0].id
    service = _get_selection_service(Session)
    service.add_project_selections(smid, [_metadata()])
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Modification)) == 1
        assert session.scalar(select(func.count()).select_from(Organism)) == 1
        assert (
            session.scalar(select(func.count()).select_from(DetectionTechnology)) == 1
        )
        assert session.scalar(select(func.count()).select_from(ProjectSelection)) == 1
        assert session.scalar(select(func.count()).select_from(Selection)) == 0
    service.add_project_selections(smid, [_metadata()])
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Modification)) == 1
        assert session.scalar(select(func.count()).select_from(Organism)) == 1
        assert (
            session.scalar(select(func.count()).select_from(DetectionTechnology)) == 1
        )
        assert session.scalar(select(func.count()).select_from(ProjectSelection)) == 1
        assert session.scalar(select(func.count()).select_from(Selection)) == 0
    # only flushed once
    assert (
        len(
            [
                m
                for m in caplog.messages
                if f"Flushed selection for project '{smid}'" in m
            ]
        )
        == 1
    )


def test_add_project_selections_other_project(Session, selection, project):  # noqa
    smid1, smid2 = project[0].id, project[1].id
    service = _get_selection_service(Session)
    service.add_project_selections(smid1, [_metadata()])
    service.add_project_selections(smid2, [_metadata()])
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(ProjectSelection)) == 2


def test_add_project_selections_is_atomic(Session, setup, project):  # noqa
    smid = project[0].id
    service = _get_selection_service(Session)
    # the second entry fails; session is rolled back
    real = SelectionService._add_project_selection_if_none
    calls = []

    def fail_on_second(*args):
        calls.append(args)
        if len(calls) == 2:
            raise RuntimeError("runtime error")
        return real(service, *args)

    service._add_project_selection_if_none = fail_on_second
    with pytest.raises(RuntimeError, match="runtime error"):
        service.add_project_selections(
            smid, [_metadata(), _metadata(modomics_id="2000000005C")]
        )
    assert len(calls) == 2
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(ProjectSelection)) == 0


def test_add_project_selections_flush_only(Session, setup, project):  # noqa
    smid = project[0].id
    service = _get_selection_service(Session)
    service.add_project_selections(smid, [_metadata()], is_flush_only=True)
    service._session.rollback()
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(ProjectSelection)) == 0


def test_get_or_create_selection_exists(Session, selection):  # noqa
    service = _get_selection_service(Session)
    selection_id = service.get_or_create_selection(1, 1, 1)
    assert selection_id == 1
    assert service._session.scalar(select(func.count()).select_from(Selection)) == 5


def test_get_or_create_selection_creates(Session, selection):  # noqa
    service = _get_selection_service(Session)
    session = service._session
    session.execute(delete(Selection))
    session.commit()
    service.get_or_create_selection(2, 1, 1)
    # flush only: caller commits
    session.rollback()
    assert session.scalar(select(func.count()).select_from(Selection)) == 0
    selection_id = service.get_or_create_selection(2, 1, 1)
    session.commit()
    row = session.get_one(Selection, selection_id)
    assert (row.modification_id, row.organism_id, row.technology_id) == (2, 1, 1)
    # idempotent
    assert service.get_or_create_selection(2, 1, 1) == selection_id


def _key(row):
    return (row["modification_id"], row["organism_id"], row["technology_id"])


EXPECTED_SELECTION = {
    "modification_id": 1,
    "rna_type": "WTS",
    "rna_type_name": "whole transcriptome",
    "modomics_short_name": "m6A",
    "technology_id": 1,
    "cls": "NGS 2nd generation",
    "meth": "Antibody-based sequencing",
    "tech": "Technology 1",
    "organism_id": 1,
    "domain": "Eukarya",
    "kingdom": "Animalia",
    "taxa_id": 9606,
    "taxa_name": "Homo sapiens",
    "taxa_short_name": "H. sapiens",
    "cto": "Cell type 1",
    "selection_id": 1,
}


def test_get_selections(Session, selection):  # noqa
    service = _get_selection_service(Session)
    selections = service.get_selections()
    assert len(selections) == 5
    assert selections[0] == EXPECTED_SELECTION


def test_get_selections_all_selections(Session, selection, project_selection):  # noqa
    # all selections with data, whatever the project selections
    service = _get_selection_service(Session)
    service._session.execute(delete(ProjectSelection).filter_by(modification_id=2))
    service._session.commit()
    assert len(service.get_selections()) == 5


def test_get_project_selections(Session, selection, project_selection):  # noqa
    # same combinations (and format) as the selections of the fixture
    service = _get_selection_service(Session)
    expected = sorted(service.get_selections(), key=_key)
    result = sorted(service.get_project_selections("12345678"), key=_key)
    assert len(result) == 5
    assert result == expected
    assert EXPECTED_SELECTION in result


def test_get_project_selections_only_project(
    Session, selection, project_selection
):  # noqa
    # selections of other projects are not returned
    service = _get_selection_service(Session)
    service._session.execute(
        delete(ProjectSelection).filter_by(modification_id=2, technology_id=1)
    )
    service._session.commit()
    result = service.get_project_selections("12345678")
    assert len(result) == 4
    assert (2, 1, 1) not in {_key(row) for row in result}
    # the selection still exists
    assert len(service.get_selections()) == 5


def test_get_project_selections_without_selection(
    Session, selection, project_selection
):  # noqa
    # no data (yet) for the combination: no selection
    service = _get_selection_service(Session)
    session = service._session
    session.execute(delete(Selection).filter_by(id=1))
    session.commit()
    result = {_key(row): row for row in service.get_project_selections("12345678")}
    assert len(result) == 5
    assert result[(1, 1, 1)] == {**EXPECTED_SELECTION, "selection_id": None}
    assert all(
        row["selection_id"] is not None
        for key, row in result.items()
        if key != (1, 1, 1)
    )
    assert len(service.get_selections()) == 4


def test_get_project_selections_other_project(
    Session, selection, project_selection
):  # noqa
    service = _get_selection_service(Session)
    assert service.get_project_selections("ABCDEFGH") == []
    assert service.get_project_selections("XXXXXXXX") == []


def test_delete_selections_by_dataset(Session, dataset):
    service = _get_selection_service(Session)
    service.delete_selections_by_dataset(dataset[0])
    assert service._gene_service.deleted_cache_list == [1, 2]
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Modification)) == 2
        assert session.scalar(select(func.count()).select_from(Organism)) == 2
        assert (
            session.scalar(select(func.count()).select_from(DetectionTechnology)) == 2
        )
        assert set(session.execute(select(Selection.id)).scalars().all()) == set(
            [3, 4, 5]
        )


def test_delete_selections_by_dataset_cache_only(Session, project, dataset):
    with Session() as session:
        new_dataset = Dataset(
            id="dataset_idXX",
            title="Dataset title X",
            organism_id=1,
            technology_id=1,
            modification_type="RNA",
            basecalling="",
            bioinformatics_workflow="",
            project_id=project[0].id,
            sequencing_platform="",
            experiment="",
            external_source="",
            date_added=datetime(2025, 1, 23, 14, 00, 00),
        )
        new_association = DatasetModificationAssociation(
            dataset_id="dataset_idXX", modification_id=1
        )
        session.add_all([new_dataset, new_association])
        session.commit()

        service = _get_selection_service(Session)
        service.delete_selections_by_dataset(dataset[0])

    assert service._gene_service.deleted_cache_list == [1, 2]

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Modification)) == 2
        assert session.scalar(select(func.count()).select_from(Organism)) == 2
        assert (
            session.scalar(select(func.count()).select_from(DetectionTechnology)) == 2
        )
        assert set(session.execute(select(Selection.id)).scalars().all()) == set(
            [1, 3, 4, 5]
        )

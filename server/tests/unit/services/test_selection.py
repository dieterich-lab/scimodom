from datetime import datetime
from sqlalchemy import func, select

from scimodom.database.models import (
    Dataset,
    DatasetModificationAssociation,
    DetectionTechnology,
    Modification,
    Organism,
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


def test_create_selection(Session, setup):
    organism = ProjectOrganismDto(
        taxa_id=9606, cto="Cell type 1", assembly_name="GRCh38", assembly_id=1
    )
    metadata = ProjectMetaDataDto(
        rna="WTS",
        modomics_id="2000000006A",
        tech="Technology 1",
        method_id="91b145ea",
        organism=organism,
        note=None,
    )
    service = _get_selection_service(Session)
    service.create_selection([metadata])

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Modification)) == 1
        assert session.scalar(select(func.count()).select_from(Organism)) == 1
        assert (
            session.scalar(select(func.count()).select_from(DetectionTechnology)) == 1
        )
        assert session.scalar(select(func.count()).select_from(Selection)) == 1


def test_create_selection_exist(Session, selection, caplog):
    organism = ProjectOrganismDto(
        taxa_id=9606, cto="Cell type 1", assembly_name="GRCh38", assembly_id=1
    )
    metadata = ProjectMetaDataDto(
        rna="WTS",
        modomics_id="2000000006A",
        tech="Technology 1",
        method_id="91b145ea",
        organism=organism,
        note=None,
    )
    service = _get_selection_service(Session)
    service.create_selection([metadata])
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Modification)) == 2
        assert session.scalar(select(func.count()).select_from(Organism)) == 2
        assert (
            session.scalar(select(func.count()).select_from(DetectionTechnology)) == 2
        )
        assert session.scalar(select(func.count()).select_from(Selection)) == 4

    assert caplog.messages == []


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
        assert set(session.execute(select(Selection.id)).scalars().all()) == set([3, 4])


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
            [1, 3, 4]
        )

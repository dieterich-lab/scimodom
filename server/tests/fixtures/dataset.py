from datetime import datetime, timezone

import pytest

from scimodom.database.models import Dataset, Data, DatasetModificationAssociation
from scimodom.utils.common_dto import Strand


@pytest.fixture
def dataset(Session, selection, project):  # noqa
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    project1_id = project[0].id
    project2_id = project[1].id
    dataset1 = Dataset(
        id="d1",
        title="dataset title",
        organism_id=1,
        technology_id=1,
        modification_type="RNA",
        basecalling="bc1",
        bioinformatics_workflow="wf1",
        project_id=project1_id,
        sequencing_platform="sp1",
        experiment="experiment 1",
        external_source="ext. source 1",
        date_added=stamp,
    )
    data1 = Data(
        id=1,
        dataset_id="d1",
        modification_id=1,
        chrom="17",
        start=100001,
        end=100002,
        name="m6A",
        score=1000,
        strand=Strand.FORWARD,
        thick_start=100001,
        thick_end=100002,
        item_rgb="128,128,0",
        coverage=43,
        frequency=100,
    )
    data2 = Data(
        id=2,
        dataset_id="d1",
        modification_id=2,
        chrom="Y",
        start=200001,
        end=200002,
        name="m5C",
        score=900,
        strand=Strand.REVERSE,
        thick_start=200001,
        thick_end=200002,
        item_rgb="0,0,128",
        coverage=44,
        frequency=99,
    )
    dataset2 = Dataset(
        id="d2",
        title="Dataset title 2",
        organism_id=2,
        technology_id=2,
        modification_type="RNA",
        basecalling="bc2",
        bioinformatics_workflow="wf2",
        project_id=project1_id,
        sequencing_platform="sp2",
        experiment="experiment 2",
        external_source="ext. source 2",
        date_added=stamp,
    )
    data3 = Data(
        id=3,
        dataset_id="d2",
        modification_id=1,
        chrom="17",
        start=100001,
        end=100002,
        name="m6A",
        score=10,
        strand=Strand.FORWARD,
        thick_start=100001,
        thick_end=100002,
        item_rgb="0,0,0",
        coverage=10,
        frequency=10,
    )
    dataset3 = Dataset(
        id="d3",
        title="Dataset title 3",
        organism_id=1,
        technology_id=2,
        modification_type="RNA",
        basecalling="",
        bioinformatics_workflow="wf3",
        project_id=project1_id,
        sequencing_platform="sp3",
        experiment="experiment 3",
        external_source="ext. source 3",
        date_added=stamp,
    )
    data4 = Data(
        id=4,
        dataset_id="d3",
        modification_id=1,
        chrom="1",
        start=20652450,
        end=20652451,
        name="m6A",
        score=0,
        strand=Strand.REVERSE,
        thick_start=20652450,
        thick_end=20652451,
        item_rgb="0,0,0",
        coverage=378,
        frequency=9,
    )
    data5 = Data(
        id=5,
        dataset_id="d3",
        modification_id=1,
        chrom="1",
        start=87328672,
        end=87328673,
        name="m6A",
        score=0,
        strand=Strand.FORWARD,
        thick_start=87328672,
        thick_end=87328673,
        item_rgb="0,0,0",
        coverage=183,
        frequency=6,
    )
    data6 = Data(
        id=6,
        dataset_id="d3",
        modification_id=1,
        chrom="1",
        start=104153268,
        end=104153269,
        name="m6A",
        score=0,
        strand=Strand.REVERSE,
        thick_start=104153268,
        thick_end=104153269,
        item_rgb="0,0,0",
        coverage=183,
        frequency=4,
    )
    data7 = Data(
        id=7,
        dataset_id="d3",
        modification_id=1,
        chrom="1",
        start=194189297,
        end=194189298,
        name="m6A",
        score=0,
        strand=Strand.FORWARD,
        thick_start=194189297,
        thick_end=194189298,
        item_rgb="0,0,0",
        coverage=19,
        frequency=47,
    )
    dataset4 = Dataset(
        id="d4",
        title="Dataset title 4",
        organism_id=2,
        technology_id=2,
        modification_type="RNA",
        basecalling="",
        bioinformatics_workflow="",
        project_id=project2_id,
        sequencing_platform="",
        experiment="",
        external_source="",
        date_added=stamp,
    )
    association1 = DatasetModificationAssociation(dataset_id="d1", modification_id=1)
    association2 = DatasetModificationAssociation(dataset_id="d1", modification_id=2)
    association3 = DatasetModificationAssociation(dataset_id="d2", modification_id=1)
    association4 = DatasetModificationAssociation(dataset_id="d3", modification_id=1)
    association5 = DatasetModificationAssociation(dataset_id="d4", modification_id=2)
    session = Session()
    session.add_all(
        [
            dataset1,
            dataset2,
            dataset3,
            dataset4,
            data1,
            data2,
            data3,
            data4,
            data5,
            data6,
            data7,
            association1,
            association2,
            association3,
            association4,
            association5,
        ]
    )
    session.commit()
    yield (dataset1, dataset2, dataset3, dataset4)

from datetime import datetime, timezone

import pytest

from scimodom.database.models import Dataset, Data, DatasetModificationAssociation
from scimodom.utils.common_dto import Strand


@pytest.fixture
def dataset(Session, selection, project):  # noqa
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    dataset1 = Dataset(
        id="d1",
        title="dataset title",
        organism_id=1,
        technology_id=1,
        modification_type="RNA",
        basecalling="bc1",
        bioinformatics_workflow="wf1",
        project_id=project.id,
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
        project_id=project.id,
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
    association1 = DatasetModificationAssociation(dataset_id="d1", modification_id=1)
    association2 = DatasetModificationAssociation(dataset_id="d1", modification_id=2)
    association3 = DatasetModificationAssociation(dataset_id="d2", modification_id=1)
    session = Session()
    session.add_all(
        [
            dataset1,
            dataset2,
            data1,
            data2,
            data3,
            association1,
            association2,
            association3,
        ]
    )
    session.commit()
    yield (dataset1, dataset2)

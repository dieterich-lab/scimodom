from datetime import datetime, timezone
from uuid import uuid4

import pytest

from scimodom.database.models import BamFile


@pytest.fixture
def bam_file(Session, dataset):
    name1 = f"{dataset[0].id}_1.bam"
    bam_file1 = BamFile(
        dataset_id=dataset[0].id,
        original_file_name=name1,
        storage_file_name=f"{dataset[0].id}_{uuid4()}_{name1}"[:256],
    )
    name2 = f"{dataset[0].id}_2.bam"
    bam_file2 = BamFile(
        dataset_id=dataset[0].id,
        original_file_name=name2,
        storage_file_name=f"{dataset[0].id}_{uuid4()}_{name2}"[:256],
    )
    name3 = f"{dataset[1].id}.bam"
    bam_file3 = BamFile(
        dataset_id=dataset[1].id,
        original_file_name=name3,
        storage_file_name=f"{dataset[1].id}_{uuid4()}_{name3}"[:256],
    )
    session = Session()
    session.add_all([bam_file1, bam_file2, bam_file3])
    session.commit()

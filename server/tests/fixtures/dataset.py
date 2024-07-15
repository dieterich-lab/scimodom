from datetime import datetime, timezone

import pytest

from scimodom.database.models import (
    Organism,
    Modomics,
    Modification,
    DetectionMethod,
    DetectionTechnology,
    Selection,
    ProjectContact,
    Project,
    Dataset,
    Data,
)
from scimodom.utils.common_dto import Strand


@pytest.fixture
def dataset(Session, setup):  # noqa
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    organism = Organism(id=1, taxa_id=9606, cto="Cell Type 1")
    modomics = Modomics(
        id="m1", name="Mod1", short_name="Mod1", moiety="moiety", reference_id=1
    )
    modification = Modification(id=1, modomics_id=modomics.id, rna="Bla")
    method = DetectionMethod(id="m1", cls="c1", meth="Method m1")
    technology = DetectionTechnology(id=1, method_id=method.id, tech="Very Cool Tech")
    selection = Selection(
        id=1,
        organism_id=organism.id,
        modification_id=modification.id,
        technology_id=technology.id,
    )
    contact = ProjectContact(
        id=1,
        contact_name="James Bond",
        contact_institution="MI5",
        contact_email="that@is.secret",
    )
    project = Project(
        id="p1",
        title="example project",
        date_published=datetime.now(),
        date_added=datetime.now(),
        summary="summary",
        contact_id=contact.id,
    )
    dataset = Dataset(
        id="d1",
        title="dataset title",
        organism_id=organism.id,
        technology_id=technology.id,
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
        modification_id=modification.id,
        chrom="17",
        start=100001,
        end=120000,
        name="Y",
        score=1000,
        strand=Strand.FORWARD,
        thick_start=100101,
        thick_end=100201,
        item_rgb="128,128,0",
        coverage=43,
        frequency=100,
    )
    data2 = Data(
        id=2,
        dataset_id="d1",
        modification_id=modification.id,
        chrom="Y",
        start=200001,
        end=220000,
        name="X",
        score=900,
        strand=Strand.REVERSE,
        thick_start=200101,
        thick_end=200201,
        item_rgb="0,0,128",
        coverage=44,
        frequency=99,
    )
    session = Session()
    session.add_all(setup)
    session.add_all(
        [
            organism,
            modomics,
            modification,
            method,
            technology,
            selection,
            contact,
            project,
            dataset,
            data1,
            data2,
        ]
    )
    session.commit()
    yield dataset

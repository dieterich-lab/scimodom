from datetime import datetime
from io import StringIO

import pytest

from scimodom.database.models import (
    Organism,
    Dataset,
    Association,
    Selection,
    Data,
    Project,
    Modification,
    Modomics,
    ProjectContact,
    DetectionTechnology,
    DetectionMethod,
)
from scimodom.services.exporter import Exporter


@pytest.fixture
def dataset(Session, setup):
    organism = Organism(id=1, taxa_id=9606, cto="Cell Type 1")
    modomics = Modomics(id="m1", name="Mod1", short_name="Mod1", moiety="moiety")
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
        modification_type="RNA",
        basecalling="bc1",
        bioinformatics_workflow="wf1",
        project_id=project.id,
        sequencing_platform="sp1",
        experiment="experiment 1",
        external_source="ext. source 1",
    )
    association = Association(id=1, dataset_id=dataset.id, selection_id=selection.id)
    data1 = Data(
        id=1,
        association_id=association.id,
        chrom="17",
        start=100001,
        end=120000,
        name="Y",
        score=1000,
        strand="+",
        thick_start=100101,
        thick_end=100201,
        item_rgb="128,128,0",
        coverage=43,
        frequency=100,
    )
    data2 = Data(
        id=2,
        association_id=association.id,
        chrom="Y",
        start=200001,
        end=220000,
        name="X",
        score=900,
        strand="-",
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
            association,
            data1,
            data2,
        ]
    )
    session.commit()
    yield dataset


def test_exporter(Session, dataset):
    exporter = Exporter(Session())
    assert exporter.get_dataset_file_name(dataset.id) == "dataset_title.bedrmod"  # noqa
    content = "".join(
        [x.decode("utf-8") for x in exporter.generate_dataset(dataset.id)]
    )

    assert (
        content
        == """#fileformat=bedRModv1.7
#organism=9606
#modification_type=RNA
#assembly=GRCh38
#annotation_source=Ensembl
#annotation_version=110
#sequencing_platform=sp1
#basecalling=bc1
#bioinformatics_workflow=wf1
#experiment=experiment 1
#external_source=ext. source 1
#chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency
17\t100001\t120000\tY\t1000\t+\t100101\t100201\t128,128,0\t43\t100
Y\t200001\t220000\tX\t900\t-\t200101\t200201\t0,0,128\t44\t99
"""
    )

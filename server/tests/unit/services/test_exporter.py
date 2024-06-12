from scimodom.services.exporter import Exporter
from fixtures.dataset import dataset  # noqa


def test_exporter(Session, dataset):  # noqa
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

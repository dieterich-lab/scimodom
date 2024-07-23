from scimodom.services.exporter import Exporter


def test_exporter(Session, dataset):  # noqa
    exporter = Exporter(Session())
    assert (
        exporter.get_dataset_file_name(dataset[0].id) == "dataset_title.bedrmod"
    )  # noqa
    content = "".join(
        [x.decode("utf-8") for x in exporter.generate_dataset(dataset[0].id)]
    )

    assert (
        content
        == """#fileformat=bedRModv1.8
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
17\t100001\t100002\tm6A\t1000\t+\t100001\t100002\t128,128,0\t43\t100
Y\t200001\t200002\tm5C\t900\t-\t200001\t200002\t0,0,128\t44\t99
"""
    )

# cf. DatasetService, Exporter
EUF = {
    "versions": ["1.6", "1.7", "1.8"],
    "1.6": {
        "headers": {
            "fileformat": "file_format",
            "organism": "taxa_id",
            "modification_type": "modification_type",
            "assembly": "assembly_name",
            "annotation_source": "annotation_source",
            "annotation_version": "annotation_version",
            "sequencing_platform": "sequencing_platform",
            "basecalling": "basecalling",
            "bioinformatics_workflow": "bioinformatics_workflow",
            "experiment": "experiment",
            "external_source": "external_source",
        },
        "required": [
            "fileformat",
            "organism",
            "modification_type",
            "assembly",
            "annotation_source",
            "annotation_version",
        ],
        "columns": {
            "chrom": "chrom",
            "chromStart": "start",
            "chromEnd": "end",
            "name": "name",
            "score": "score",
            "strand": "strand",
            "thickStart": "thick_start",
            "thickEnd": "thick_end",
            "itemRgb": "item_rgb",
            "coverage": "coverage",
            "frequency": "frequency",
            "refBase": "ref_base",
        },
    },
    "1.7": {
        "headers": {
            "fileformat": "file_format",
            "organism": "taxa_id",
            "modification_type": "modification_type",
            "assembly": "assembly_name",
            "annotation_source": "annotation_source",
            "annotation_version": "annotation_version",
            "sequencing_platform": "sequencing_platform",
            "basecalling": "basecalling",
            "bioinformatics_workflow": "bioinformatics_workflow",
            "experiment": "experiment",
            "external_source": "external_source",
        },
        "required": [
            "fileformat",
            "organism",
            "modification_type",
            "assembly",
            "annotation_source",
            "annotation_version",
        ],
    },
    "1.8": {
        "headers": {
            "fileformat": "file_format",
            "organism": "taxa_id",
            "modification_type": "modification_type",
            "assembly": "assembly_name",
            "annotation_source": "annotation_source",
            "annotation_version": "annotation_version",
            "sequencing_platform": "sequencing_platform",
            "basecalling": "basecalling",
            "bioinformatics_workflow": "bioinformatics_workflow",
            "experiment": "experiment",
            "external_source": "external_source",
        },
        "required": [
            "fileformat",
            "organism",
            "modification_type",
            "assembly",
            "annotation_source",
            "annotation_version",
        ],
    },
}

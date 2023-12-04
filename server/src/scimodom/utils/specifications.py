"""Sci-Modom specifications and other constants/parameters
"""

# ID length
SMID_LENGTH = 8
EUFID_LENGTH = 12
ASSEMBLY_NUM_LENGTH = 12

# EUF
specsEUF = {
    "format": "bedRMod",
    "header": {"comment": "#", "delimiter": "="},
    "delimiter": "\t",
    "1.6": {
        "headers": {
            "fileformat": "file_format",
            "organism": "taxa_id",
            "modification_type": "modification_type",
            "assembly": "assembly_id",
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
}

# Annotation
ANNOTATION_URL = "https://ftp.ensembl.org/pub"

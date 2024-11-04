"""EUF specifications.
This module defines which versions are fully compatible with Sci-ModoM.

Compatibility does not only refer to the header section, but also to
the data section, and how data records are handled using DTOs, ORM models, etc.
cf. DatasetService (import), Exporter.
"""

EUF_VERSION: str = "1.8"
EUF_COMPATIBLE_VERSIONS: list[str] = ["1.8"]
EUF_HEADERS: dict[str, str] = {
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
}
EUF_REQUIRED_HEADERS: list[str] = [
    "fileformat",
    "organism",
    "modification_type",
    "assembly",
    "annotation_source",
    "annotation_version",
]

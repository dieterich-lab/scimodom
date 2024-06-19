from datetime import datetime

from scimodom.utils.project_dto import ProjectTemplate

EXAMPLE_TEMPLATE = """
{
    "title": "Title",
    "summary": "Summary",
    "contact_name": "Name",
    "contact_institution": "Institution",
    "contact_email": "x@example.com",
    "date_published": "2023-07-12",
    "external_sources": {
        "doi": "doi",
        "pmid": "123"
    },
    "metadata": [
        {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "m6A-SAC-seq",
            "method_id": "e00d694d",
            "organism": {"taxa_id": 9606, "cto": "HeLa", "assembly": "GRCh38"}
        },
        {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "m6A-SAC-seq",
            "method_id": "e00d694d",
            "organism": {"taxa_id": 9606, "cto": "HEK293", "assembly": "GRCh38"}
        }
    ]
}
"""


def test_project_template_simple():
    template = ProjectTemplate.model_validate_json(EXAMPLE_TEMPLATE)
    assert template.external_sources[0].doi == "doi"
    assert template.date_published == datetime(2023, 7, 12)
    assert template.contact_email == "x@example.com"
    assert template.metadata[1].organism.cto == "HEK293"


EXAMPLE_TEMPLATE_NO_EXTERNAL_SOURCES = """
{
    "title": "Title",
    "summary": "Summary",
    "contact_name": "Name",
    "contact_institution": "Institution",
    "contact_email": "x@example.com",
    "date_published": "2023-07-12",
    "metadata": [
        {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "m6A-SAC-seq",
            "method_id": "e00d694d",
            "organism": {"taxa_id": 9606, "cto": "HeLa", "assembly": "GRCh38"}
        },
        {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "m6A-SAC-seq",
            "method_id": "e00d694d",
            "organism": {"taxa_id": 9606, "cto": "HEK293", "assembly": "GRCh38"}
        }
    ]
}
"""


def test_project_template_no_external_source():
    template = ProjectTemplate.model_validate_json(EXAMPLE_TEMPLATE_NO_EXTERNAL_SOURCES)
    assert template.external_sources == []

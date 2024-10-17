from datetime import datetime

import pytest
from pydantic import ValidationError

from scimodom.utils.dtos.project import (
    ProjectSourceDto,
    ProjectOrganismDto,
    ProjectMetaDataDto,
    ProjectTemplate,
)


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
            "organism": {"taxa_id": 9606, "cto": "HeLa", "assembly_name": "GRCh38"}
        },
        {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "m6A-SAC-seq",
            "method_id": "e00d694d",
            "organism": {"taxa_id": 9606, "cto": "HEK293", "assembly_name": "GRCh38"}
        }
    ]
}
"""

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
            "organism": {"taxa_id": 9606, "cto": "HeLa", "assembly_name": "GRCh38"}
        },
        {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "m6A-SAC-seq",
            "method_id": "e00d694d",
            "organism": {"taxa_id": 9606, "cto": "HEK293", "assembly_name": "GRCh38"}
        }
    ]
}
"""

EXAMPLE_TEMPLATE_NO_METADATA = """
{
    "title": "Title",
    "summary": "Summary",
    "contact_name": "Name",
    "contact_institution": "Institution",
    "contact_email": "x@example.com",
    "date_published": "2023-07-12",
    "metadata": null
}
"""


# tests


def test_project_source_validator():
    ProjectSourceDto(doi=None, pmid="12345678")


@pytest.mark.parametrize(
    "doi,pmid",
    [
        ("", 12345678),
        ("10.nnnnnn/example", 0),
        (None, None),
    ],
)
def test_project_source_dto(doi, pmid):
    with pytest.raises(ValidationError):
        ProjectSourceDto(doi=doi, pmid=pmid)


@pytest.mark.parametrize(
    "taxid,cto,name",
    [
        (0, "cell type A", "GRCh38"),
        (9606, "", "GRCh38"),
        (
            9606,
            "cell type A",
            "FGIBGV2VB927FN9ST2G1VV7GNLZD6P54NNJVOKU7TC5W8LDY94G5GXLTDAVRJLBBHRXY4H8E5WHAPD1A5NJZGL68O6ZOCFAXWOQ4SBODC9KECUTHOOZV1MUDWYMHZTEFCBGXC01QZXTQG4K0TK9DF0WQFP6PRHLHJO3GA3V30A15OOSISW545T9AY83Q4LNWSYZTKEV9Y0PA1ALWU1YYC30DUWJHTTE8U9A2SRC4FWCBLYJK62WV6",
        ),
    ],
)
def test_project_organism_dto(taxid, cto, name):
    with pytest.raises(ValidationError):
        ProjectOrganismDto(taxa_id=taxid, cto=cto, assembly_name=name, assembly_id=None)


@pytest.mark.parametrize(
    "mod,meth",
    [
        (1, "12345678"),
        ("12345678", "123456789"),
    ],
)
def test_project_metadata_dto(mod, meth):
    organism = ProjectOrganismDto(
        taxa_id=9606, cto="Cell B", assembly_name="GRCh38", assembly_id=1
    )
    with pytest.raises(ValidationError):
        ProjectMetaDataDto(
            rna="RNA",
            modomics_id=mod,
            tech="Technology",
            method_id=meth,
            organism=organism,
        )


def test_project_template():
    template = ProjectTemplate.model_validate_json(EXAMPLE_TEMPLATE)
    assert template.external_sources[0].doi == "doi"
    assert template.date_published == datetime(2023, 7, 12)
    assert template.contact_email == "x@example.com"
    assert template.metadata[1].organism.cto == "HEK293"


def test_project_template_no_external_source():
    template = ProjectTemplate.model_validate_json(EXAMPLE_TEMPLATE_NO_EXTERNAL_SOURCES)
    assert template.external_sources == []


def test_project_template_no_metadata():
    with pytest.raises(ValidationError):
        ProjectTemplate.model_validate_json(EXAMPLE_TEMPLATE_NO_METADATA)

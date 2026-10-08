from io import StringIO
from typing import Iterable

import pytest

from scimodom.api.catalog import catalog_api
from scimodom.services.annotation import (
    AnnotationService,
    EnsemblAnnotationService,
)
from scimodom.services.assembly import AssemblyService
from scimodom.services.gene import GeneService
from scimodom.services.url import CATALOG_API_ROUTE
from scimodom.services.utilities import UtilitiesService
from scimodom.utils.specs.enums import AnnotationSource, AssemblyFileType
from tests.api.schematise import validate, client_fixture

SCHEMA = "catalog.yaml"

client = client_fixture(catalog_api, CATALOG_API_ROUTE)


class MockFileService:
    CHROM_SIZES = """1\t248956422"""

    @staticmethod
    def open_assembly_file(taxa_id: int, file_type: AssemblyFileType) -> StringIO:
        return StringIO(MockFileService.CHROM_SIZES)

    @staticmethod
    def get_gene_cache(selection_id: int) -> Iterable[str]:
        return ["GENE1", "GENE2"]


@pytest.fixture
def services(Session, selection, mocker):
    utilities_service = UtilitiesService(Session())
    mocker.patch(
        "scimodom.api.catalog.get_utilities_service",
        return_value=utilities_service,
    )
    mocker.patch(
        "scimodom.api.helpers.validation.get_utilities_service",
        return_value=utilities_service,
    )
    annotation_service = AnnotationService(
        session=Session(),
        services_by_annotation_source={
            AnnotationSource.ENSEMBL: EnsemblAnnotationService(
                session=Session(),
                data_service=mocker.Mock(),
                bedtools_service=mocker.Mock(),
                external_service=mocker.Mock(),
                web_service=mocker.Mock(),
                gene_service=mocker.Mock(),
                file_service=mocker.Mock(),
            ),
        },
    )
    mocker.patch(
        "scimodom.api.catalog.get_annotation_service",
        return_value=annotation_service,
    )
    assembly_service = AssemblyService(
        session=Session(),
        external_service=mocker.Mock(),
        web_service=mocker.Mock(),
        file_service=MockFileService(),
    )
    mocker.patch(
        "scimodom.api.catalog.get_assembly_service",
        return_value=assembly_service,
    )
    gene_service = GeneService(session=Session(), file_service=MockFileService())
    mocker.patch(
        "scimodom.api.catalog.get_gene_service",
        return_value=gene_service,
    )


def prefix_url(path: str) -> str:
    return f"{CATALOG_API_ROUTE}{path}"


@pytest.mark.parametrize(
    "url",
    [
        "/rna-types",
        "/rna-types/WTS/biotypes",
        "/taxa",
        "/modomics",
        "/methods",
        "/selections",
    ],
)
def test_catalogs_schema(client, services, url):
    response = client.get(prefix_url(url))
    assert response.json
    validate(SCHEMA, response, 200)


def test_features_schema(client, services):
    response = client.get(prefix_url("/rna-types/WTS/features"))
    assert response.json
    validate(SCHEMA, response, 200)


def test_chroms_schema(client, services):
    response = client.get(prefix_url("/taxa/9606/chromosomes"))
    assert response.json
    validate(SCHEMA, response, 200)


def test_assemblies_schema(client, services):
    response = client.get(prefix_url("/taxa/9606/assemblies"))
    assert response.json
    validate(SCHEMA, response, 200)


def test_genes_schema(client, services):
    response = client.get(prefix_url("/genes?selection=1"))
    assert response.json
    validate(SCHEMA, response, 200)

from datetime import datetime
from pathlib import Path
import re

import pytest
from flask import Flask
from sqlalchemy import func, select

from scimodom.database.models import (
    DataAnnotation,
    Data,
    DatasetModificationAssociation,
    Dataset,
    GenomicAnnotation,
    Project,
)
from scimodom.cli.assembly import assembly_cli
from scimodom.cli.charts import charts_cli
from scimodom.services.annotation import AnnotationService
from scimodom.services.annotation.ensembl import EnsemblAnnotationService
from scimodom.services.assembly import AssemblyService
from scimodom.services.bedtools import BedToolsService
from scimodom.services.data import DataService
from scimodom.services.dataset import DatasetService
from scimodom.services.external import ExternalService
from scimodom.services.gene import GeneService
from scimodom.services.file import FileService
from scimodom.services.project import ProjectService
from scimodom.services.selection import SelectionService
from scimodom.services.sunburst import SunburstService
from scimodom.services.validator import ValidatorService
from scimodom.services.web import WebService
from scimodom.utils.specs.enums import AnnotationSource, SunburstChartType
from tests.mocks.enums import MockEnsembl


def _get_file_service(Session, tmp_path):
    return FileService(
        session=Session(),
        data_path=Path(tmp_path, "t_data"),
        temp_path=Path(tmp_path, "t_temp"),
        upload_path=Path(tmp_path, "t_upload"),
        import_path=Path(tmp_path, "t_import"),
    )


def _get_assembly_service(Session, tmp_path):
    return AssemblyService(
        session=Session(),
        external_service=ExternalService(
            file_service=_get_file_service(Session, tmp_path)
        ),
        web_service=WebService(),
        file_service=_get_file_service(Session, tmp_path),
    )


@pytest.fixture
def test_runner():
    app = Flask(__name__)
    app.register_blueprint(assembly_cli)
    yield app.test_cli_runner()


@pytest.fixture
def mock_services(mocker, Session, tmp_path):
    mocker.patch("scimodom.services.assembly.Ensembl", MockEnsembl)
    mocker.patch(
        "scimodom.cli.assembly.get_assembly_service",
        return_value=_get_assembly_service(Session, tmp_path),
    )


# tests


def test_add_assembly(Session, test_runner, setup, mock_services):
    result = test_runner.invoke(args=["assembly", "add", "1"], input="y")
    # exceptions are handled gracefully so exit code will likely always be 0...
    assert result.exit_code == 0

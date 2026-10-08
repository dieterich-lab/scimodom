from scimodom.api.upload import upload_api
from scimodom.services.url import UPLOAD_API_ROUTE
from tests.api.schematise import validate, client_fixture

SCHEMA = "upload.yaml"
client = client_fixture(upload_api, UPLOAD_API_ROUTE)


def prefix_url(path: str) -> str:
    return f"{UPLOAD_API_ROUTE}{path}"


def test_upload_schema(client, mocker):
    service = mocker.Mock()
    service.upload_tmp_file.return_value = "abcdef123456"
    mocker.patch("scimodom.api.upload.get_file_service", return_value=service)
    response = client.post(prefix_url("/uploads"), data=b"chrom\tstart\n")
    validate(SCHEMA, response, 201)

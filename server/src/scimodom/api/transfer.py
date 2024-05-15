from flask import Blueprint, Response, stream_with_context, request
from flask_cors import cross_origin

from scimodom.services.exporter import get_exporter, NoSuchDataset
from scimodom.services.file import FileService

transfer_api = Blueprint("transfer_api", __name__)


@transfer_api.route("/dataset/<dataset_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def export_dataset(dataset_id: str):
    exporter = get_exporter()
    try:
        file_name = exporter.get_dataset_file_name(dataset_id)
        return Response(
            stream_with_context(exporter.generate_dataset(dataset_id)),
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )
    except NoSuchDataset as exc:
        return {"message": str(exc)}, 404


@transfer_api.route("/tmp_upload", methods=["POST"])
@cross_origin(supports_credentials=True)
def upload_tmp_file():
    try:
        rfile = request.files["file"]
    except KeyError:
        return {"message": "Bad Request"}, 400
    else:
        return FileService.upload_default(rfile)

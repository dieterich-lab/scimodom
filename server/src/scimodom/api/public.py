import os
from pathlib import Path

from flask import Blueprint, request
from flask_cors import cross_origin

from scimodom.services.public import get_public_service

api = Blueprint("api", __name__)


@api.route("/modification", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_modification():
    public_service = get_public_service()
    return public_service.get_modomics()


@api.route("/smid", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_smid():
    public_service = get_public_service()
    return public_service.get_project()


@api.route("/method", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_method():
    public_service = get_public_service()
    return public_service.get_detection_method()


@api.route("/taxid", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_taxid():
    public_service = get_public_service()
    return public_service.get_taxa()


@api.route("/assembly/<taxid>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_assembly(taxid):
    public_service = get_public_service()
    return public_service.get_assembly_for_taxid(taxid)


@api.route("/selection", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_selection():
    public_service = get_public_service()
    return public_service.get_selection()


@api.route("/chrom/<taxid>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_chrom(taxid):
    public_service = get_public_service()
    return public_service.get_chrom(taxid)


@api.route("/search", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_search():
    """Search view API."""
    selection_ids = request.args.getlist("selection", type=int)
    taxa_id = request.args.get("taxid", type=int)
    chrom = request.args.get("chrom", type=str)
    chrom_start = request.args.get("chromStart", type=int)
    chrom_end = request.args.get("chromEnd", type=int)
    first_record = request.args.get("firstRecord", type=int)
    max_records = request.args.get("maxRecords", type=int)
    multi_sort = request.args.getlist("multiSort", type=str)
    table_filter = request.args.getlist("tableFilter", type=str)

    public_service = get_public_service()
    response = public_service.get_search(
        selection_ids,
        taxa_id,
        chrom,
        chrom_start,
        chrom_end,
        first_record,
        max_records,
        multi_sort,
        table_filter,
    )
    return response


@api.route("/browse", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_browse():
    """Browse view API."""
    public_service = get_public_service()
    return public_service.get_dataset()


@api.route("/compare/<step>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_compare(step):
    """Compare view API."""
    dataset_ids_a = request.args.getlist("datasetIdsA", type=str)
    dataset_ids_b = request.args.getlist("datasetIdsB", type=str)
    dataset_upload = request.args.get("datasetUpload", type=str)
    query_operation = request.args.get("queryOperation", type=str)

    public_service = get_public_service()
    response = public_service.get_comparison(
        step, dataset_ids_a, dataset_ids_b, dataset_upload, query_operation
    )
    return response


@api.route("/upload", methods=["POST"])
@cross_origin(supports_credentials=True)
def upload_file():
    # TODO: define app.config['UPLOAD_PATH'] = UPLOAD_FOLDER
    # ALLOWED_EXTENSIONS are dealt with PrimeVue FileUpload
    # PEP8 import
    from werkzeug.utils import secure_filename

    upload = os.getenv("UPLOAD_PATH")
    if "file" not in request.files:
        # this shouldn't happen, but ...
        pass
    # or empty file without a filename should not happen
    rfile = request.files["file"]
    filename = secure_filename(rfile.filename)
    response = Path(upload, filename)
    rfile.save(response)

    return response.as_posix()

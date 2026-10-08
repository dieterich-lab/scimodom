from decimal import Decimal

from flask import Flask, jsonify

from scimodom.api.helpers.serialisation import set_json_provider
from scimodom.api.modification import (
    FIELDS_TO_CSV_HEADER_MAP,
    _get_csv_from_modification_records,
)
from scimodom.utils.specs.enums import Strand


def test_decimal_is_a_json_number():
    app = Flask(__name__)
    set_json_provider(app)

    @app.get("/")
    def index():
        return {
            "records": [{"frequency": Decimal(f)} for f in ("5.00", "5.40", "5.45")]
        }

    @app.get("/jsonify")
    def explicit():
        return jsonify({"frequency": Decimal("100.00")})

    response = app.test_client().get("/")
    assert (
        response.get_data(as_text=True)
        == '{"records":[{"frequency":5.0},{"frequency":5.4},{"frequency":5.45}]}\n'
    )
    assert app.test_client().get("/jsonify").json == {"frequency": 100.0}


def test_csv_export_keeps_the_decimal_text():
    # the CSV is written from the Decimal, not from the JSON: "5.00" stays "5.00"
    record = {key: 1 for key in FIELDS_TO_CSV_HEADER_MAP}
    record["strand"] = Strand.FORWARD
    record["frequency"] = Decimal("5.00")
    lines = _get_csv_from_modification_records([record]).splitlines()
    header = lines[0].split(",")
    assert lines[1].split(",")[header.index("frequency")] == "5.00"

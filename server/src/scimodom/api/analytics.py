from flask import Blueprint, Response

from scimodom.services.sunburst import get_sunburst_service

from scimodom.api.helpers import (
    ClientResponseException,
    parse_valid_sunburst_type,
)

analytics_api = Blueprint("analytics_api", __name__)

BUFFER_SIZE = 1024 * 1024


@analytics_api.get("/charts/sunbursts/<sunburst_type>")
def get_sunburst_chart(sunburst_type):
    """Get sunburst chart data.

    :param sunburst_type: Sunburst chart type
    :return: JSON object to generate one of the
    sunburst charts.
    :statuscode 200: OK
    :statuscode 400: Bad Request - invalid chart type
    :statuscode 500: Internal Server Error
    """
    try:
        valid_sunburst_type = parse_valid_sunburst_type(sunburst_type)
        sunburst_service = get_sunburst_service()
    except ClientResponseException as exc:
        return exc.response_tuple

    def generate():
        with sunburst_service.open_json(valid_sunburst_type) as fp:
            while True:
                buffer = fp.read(BUFFER_SIZE)
                if len(buffer) == 0:
                    break
                yield buffer

    return Response(
        generate(),
        mimetype="application/json",
    )

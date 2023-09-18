import json
from sqlalchemy import select

from flask_cors import cross_origin

from scimodom.database.models import Modomics
from scimodom.database.database import get_session

from . import api


@api.route("/modification/<string:mod>")
@cross_origin(supports_credentials=True)
def get_mod(mod):
    values = (
        get_session()
        .execute(select(Modomics).where(Modomics.short_name == mod))
        .first()
    )
    results = [{"id": value.id, "name": value.name} for value in values]

    # http://127.0.0.1:5000/api/v0/modification/m6A
    return (json.dumps(results), 200, {"content_type": "application/json"})

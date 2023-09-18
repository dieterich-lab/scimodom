import json
from sqlalchemy import select

from flask import request, jsonify

from flask_cors import cross_origin

# from scimodom.database.models import

from scimodom.database.models import Taxonomy

from scimodom import create_app

from scimodom.database.database import get_session


app = create_app()


# TODO: to controller


# @app.route("/", methods=["POST"])
# @cross_origin(supports_credentials=True)
# def hello():
# project = request.get_json()
## if "modification" in project.keys():
## return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
## else:
# print(project)
# return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
## return (json.dumps({ 'message': "Hello world!" }),
## 200, { 'content_type': 'application/json'})

# @app.route("/")
# def hello_world():
# return "<p>Hello, World!</p>"


# @app.route("/test")
@app.route("/")
@cross_origin(supports_credentials=True)
def test():
    # values = app.session.execute(
    # select(Taxonomy)
    # ).scalars().all()

    values = get_session().execute(select(Taxonomy)).scalars().all()

    results = [
        {"domain": value.domain, "kingdom": value.kingdom, "phylum": value.phylum}
        for value in values
    ]

    return (json.dumps(results), 200, {"content_type": "application/json"})

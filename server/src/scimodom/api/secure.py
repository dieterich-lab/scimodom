from flask import request

# from flask_jwt_extended import jwt_required

from . import api


@api.route("/secure", methods=["GET"])
# @jwt_required
def secured_endpoint():
    pass

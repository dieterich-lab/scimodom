from flask import Blueprint

api = Blueprint("api", __name__)

# E402 module level import not at top of file
from . import queries

from flask import Flask
from scimodom.api.helpers.serialisation import set_json_provider

app = None


def create_app_singleton():
    """Create application."""
    global app
    app = Flask("scimodom")
    set_json_provider(app)
    return app

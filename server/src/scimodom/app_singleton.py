from flask import Flask

app = None


def create_app_singleton():
    global app
    app = Flask("scimodom")
    return app

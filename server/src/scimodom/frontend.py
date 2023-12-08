#
# This module will just serve the files generated by VUE
# as static content. In the DEV setup it is not used.
#
#
from flask import Blueprint
from scimodom.config import Config

frontend = Blueprint("frontend", __name__, static_folder=Config.FRONTEND_PATH)


@frontend.route('/')
def index():
    return frontend.send_static_file('index.html')


@frontend.route('/<path:filename>')
def assets(filename):
    print(filename)
    return frontend.send_static_file(filename)

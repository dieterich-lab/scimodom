# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from pathlib import Path

# Add docs/source to sys.path to resolve the local module import.
sys.path.insert(0, str(Path(__file__).parent))

import scimodom  # noqa: E402
import include_swagger_api_spec  # noqa: E402

project = "Sci-ModoM Docs"
copyright = "2023 under the terms of the GNU AGPLv3+ License."
author = "Etienne Boileau"
version = scimodom.__version__
release = scimodom.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinxarg.ext",
    "sphinx_copybutton",
    "sphinx_issues",
    "swagger_plugin_for_sphinx",
]
issues_github_path = "dieterich-lab/scimodom"
templates_path = ["_templates"]
exclude_patterns = []

# Write the Swagger API specifications.
include_swagger_api_spec.write()

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = ""
html_static_path = ["_static"]
html_theme_options = {
    "light_logo": "logo.png",
    "dark_logo": "logo_dark.png",
}
html_favicon = "_static/favicon.ico"

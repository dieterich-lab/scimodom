import json
from pathlib import Path

from scimodom.config import Config
from scimodom.database.database import get_session
from scimodom.services.project import ProjectService
import scimodom.utils.utils as utils


def add_project(project_template: str | Path) -> None:
    """Provides CLI function to add new project.

    :param project_template: Path to a json file with
    require fields.
    :type project_template: str or Path
    """
    session = get_session()
    # load project metadata
    project = json.load(open(project_template))
    # add project
    msg = f"Adding project {project_template} to {Config.DATABASE_URI}..."
    if not utils.confirm(msg):
        return
    service = ProjectService(session, project)
    service.create_project()

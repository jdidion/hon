from pathlib import Path
from typing import Optional

import click

from hon.project import Project
from hon.tools.poetry import Poetry


def create(ctx: click.Context, name: str, parent: Optional[Path] = None):
    """
    Create a new project.

    Args:
        name: The project name.
        parent: The parent directory; defaults to the current working directory.
    """
    if parent is None:
        parent = Path.cwd()

    project_dir = parent / name
    if project_dir.exists():
        raise ValueError(f"Directory {project_dir} already exists")
    else:
        project_dir.mkdir(parents=True)

    # Call the `poetry init` command, which should result in
    # the creation of the pyproject.toml file
    poetry = Poetry(ctx.obj["config"].get_tool("poetry"))
    poetry.init(name, project_dir)

    # Create the default project files
    project = Project(project_dir)
    project.create_from_templates()

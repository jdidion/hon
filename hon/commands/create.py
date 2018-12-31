from pathlib import Path
from typing import Optional

from click import Context
from git import Repo

from hon.project import Project
from hon.tools.poetry import Poetry


def create(ctx: Context, name: str, parent: Optional[Path] = None):
    """
    Create a new project.

    Args:
        ctx: The Click context.
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

    git_repo = Repo.init(str(project_dir))

    # Call the `poetry init` command, which should result in
    # the creation of the pyproject.toml file
    poetry = Poetry(ctx.obj["config"].get_tool("poetry"))
    poetry.init(name, project_dir)

    project = Project(project_dir, git_repo=git_repo)

    # Create the default project files
    project.create_from_templates()

    # Add all the newly created files to the git staging area
    project.add_all_untracked()

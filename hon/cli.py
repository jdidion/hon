from pathlib import Path
from typing import Optional, Sequence

import autoclick as ac
import click
from git import Repo

from hon.config import Config
from hon.project import Project
from hon.tools.poetry import Poetry


def get_project(ctx: click.Context):
    return ctx.obj["project"]


@ac.group(pass_context=True)
def hon(
    ctx: click.Context, project: Optional[Path] = None,
    config: Optional[ac.ReadableDir] = None
):
    """
    Base command. Parses pyproject.toml and adds it to the context.

    Args:
        ctx: The click context.
        project: The project directory. Defaults to the current working directory.
        config: Configuration directory; defaults to `$HOME/.hon`.
    """
    ctx.ensure_object(dict)

    if project is None:
        project = Path.cwd()
    try:
        ctx.obj["project"] = Project(project)
    except FileNotFoundError:
        pass

    ctx.obj["config"] = Config(config)


@hon.command()
def create(ctx: click.Context, name: str, parent: Optional[Path] = None):
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

    # Now initialize the project directory
    project = Project(project_dir, git_repo=git_repo)
    project.init()


@hon.command(pass_context=True)
def build(ctx: click.Context, install: bool = False, debug: bool = False):
    """
    Builds the project using poetry.

    Args:
        ctx: The Click context.
        install: Install the project wheel after building it.
        debug: Show verbose output for debugging.
    """
    project = get_project(ctx)
    project.build(install=install, debug=debug)


@hon.command(pass_context=True)
def install(ctx: click.Context):
    """
    Installs the project wheel into the virtualenv.

    Args:
        ctx: The Click context.
    """
    project = get_project(ctx)
    project.install()


@hon.group(pass_context=True)
def dep(ctx: click.Context):
    pass


@dep.command(pass_context=True)
def add(
    ctx: click.Context, names: Optional[Sequence[str]] = None, exact: bool = False,
    dev: bool = False, optional: bool = False
):
    """
    Add a dependency.

    Args:
        ctx: The Click context.
        names: The names of packages to install, including any version constriants.
            If no names are specified, an interactive search is performed.
        exact: Whether the names and versions should be interpreted strictly. If
            unset, a search is performed for dependencies that fail to resolve.
        dev: Whether to add these as development dependencies.
        optional: Whether to add these as optional dependencies.
    """
    project = get_project(ctx)
    if not names:
        project.add_dependency(dev=dev, optional=optional)
    else:
        for name in names:
            project.add_dependency(name, exact=exact, dev=dev, optional=optional)


@dep.command(pass_context=True)
def remove(ctx: click.Context, names: Sequence[str], dev: bool = False):
    project = get_project(ctx)
    for name in names:
        project.remove_dependency(name, dev=dev)


@dep.command(pass_context=True)
def update(ctx: click.Context, dev: bool = True):
    project = get_project(ctx)
    project.update_dependencies(dev=dev)


@dep.command(pass_context=True)
def lock(ctx: click.Context):
    project = get_project(ctx)
    project.lock_dependencies()


@hon.command()
def test(
    ctx: click.Context,
    tests: Optional[Sequence[str]] = None,
    debug: bool = False
):
    """
    Run unit tests using pytest.

    Args:
        tests: The tests to run.
        debug: Show verbose output.

    Returns:

    """
    project = get_project(ctx)
    project.test(tests=tests, debug=debug)

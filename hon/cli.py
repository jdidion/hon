from pathlib import Path
from typing import Optional

import autoclick as ac
import click

from hon.commands import COMMANDS
from hon.config import Config
from hon.project import Project


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


for cmd in COMMANDS:
    hon.command(decorated=cmd, pass_context=True)

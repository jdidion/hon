from hon.utils import run

import click


def build(ctx: click.Context, debug: bool = False):
    """
    Builds the project using poetry.

    Args:
        debug: Show verbose output for debugging.
    """
    cmd = ["poetry"]
    if debug:
        cmd.append("-vvv")
    cmd.append("build")
    run(cmd)
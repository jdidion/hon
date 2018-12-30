from typing import Sequence, Optional

import click

from hon.utils import run


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
    cmd = ["pytest", "--cov", "--cov-report", "term-missing"]
    if debug:
        cmd.extend(["-s", "-vv", "--full-trace"])
    else:
        cmd.append("--show-capture=all")
    if tests:
        cmd.extend(tests)
    run(cmd)

from contextlib import contextmanager
import os
from pathlib import Path

import tomlkit


def read_toml(path: Path):
    with open(path, "rt") as inp:
        return tomlkit.parse(inp.read())


@contextmanager
def chdir(target: Path):
    curwd = Path.cwd()
    try:
        os.chdir(target)
        yield
    finally:
        os.chdir(curwd)

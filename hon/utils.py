from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys

import tomlkit


def read_toml(path: Path):
    with open(path, "rt") as inp:
        return tomlkit.parse(inp.read())


def run(cmd, echo: bool = True, **kwargs) -> subprocess.CompletedProcess:
    if echo:
        if "stdin" not in kwargs:
            kwargs["stdin"] = sys.stdin
        if "stdout" not in kwargs:
            kwargs["stdout"] = sys.stdout
        if "stderr" not in kwargs:
            kwargs["stderr"] = sys.stderr
    return subprocess.run(cmd, **kwargs)


@contextmanager
def chdir(target: Path):
    curwd = Path.cwd()
    try:
        os.chdir(target)
        yield
    finally:
        os.chdir(curwd)

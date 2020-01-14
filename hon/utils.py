from contextlib import contextmanager
import os
from pathlib import Path
from shlex import quote
import subprocess
import sys
from typing import IO, List, Union

import toml


def read_toml(path: Path):
    with open(path, "rt") as inp:
        toml.load(inp)


@contextmanager
def chdir(target: Path):
    curwd = Path.cwd()
    try:
        os.chdir(target)
        yield
    finally:
        os.chdir(curwd)


def run_cmd(
    cmd: List[str],
    stdout: Union[bool, IO, None] = None,
    stderr: Union[bool, IO, None] = None,
    shell: bool = False,
    **kwargs
):
    """
    Execute a command in a subprocess.

    Args:
        cmd: List of command arguments.
        stdout: If True, capture stdout and return it. If None, forward stdout to
            sys.stdout. If a file-like object, write stdout to the file.
        stderr: If True, capture stderr and return it. If None, forward stderr to
            sys.stdout. If a file-like object, write stderr to the file.
        shell: Whether to execute the command using a shell.
        **kwargs: Additional kwargs to `subprocess.check_output`.

    Returns:
        A tuple (stdout, stderr). Each will be None unless their respective
        parameters were set to True.
    """
    if stdout is None:
        kwargs["stdout"] = sys.stdout
        proc_fn = subprocess.check_call
    else:
        proc_fn = subprocess.check_output
        if stdout is True:
            kwargs["stdout"] = subprocess.PIPE

    if stderr is None:
        kwargs["stderr"] = sys.stderr
    elif stderr is True:
        kwargs["stderr"] = subprocess.PIPE

    if shell:
        cmd_str = " ".join(quote(arg) for arg in cmd)
        if "executable" not in kwargs:
            kwargs["executable"] = "/bin/bash"
        return proc_fn(cmd_str, shell=True, **kwargs)
    else:
        return proc_fn(cmd, shell=False, **kwargs)

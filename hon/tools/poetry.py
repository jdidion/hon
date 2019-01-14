from pathlib import Path
from typing import Optional

import delegator


class Poetry:
    def __init__(
        self, executable: Optional[str] = "poetry", working_dir: Optional[Path] = None
    ):
        self._executable = executable
        self.working_dir = working_dir or Path.cwd()

    def init(self, name: str):
        self._run_command("init", "--name", name)

    def build(self, **kwargs):
        self._run_command("build", **kwargs)

    def add(
        self, name: str, dev: bool = False, optional: bool = False,
        python_version: Optional[str] = None, **kwargs
    ):
        cmd = ["add"]
        if dev:
            cmd.append("--dev")
        if optional:
            cmd.append("--optional")
        if python_version:
            cmd.extend(["--python", python_version])
        cmd.append(name)
        self._run_command(*cmd, **kwargs)

    def remove(self, name: str, dev: bool = False, **kwargs):
        cmd = ["remove"]
        if dev:
            cmd.append("--dev")
        cmd.append(name)
        self._run_command(*cmd, **kwargs)

    def update(self, dev: bool = False, **kwargs):
        cmd = ["update"]
        if not dev:
            cmd.append("--no-dev")
        self._run_command(*cmd, **kwargs)

    def search(self, name: str, **kwargs):
        self._run_command("search", name, **kwargs)

    def lock(self, **kwargs):
        self._run_command("lock", **kwargs)

    def _run_command(self, *args, **kwargs):
        cmd = self._get_command(**kwargs)
        cmd.extend(args)
        delegator.run(cmd, cwd=self.working_dir)

    def _get_command(self, debug: bool = False):
        cmd = [self._executable]
        if debug:
            cmd.append("-vvv")
        return cmd

from pathlib import Path

from hon.utils import run


class Poetry:
    def __init__(self, executable: str):
        self._executable = executable

    def init(self, name: str, project_dir: Path):
        cmd = [self._executable, "init", "--name", name]
        run(cmd, cwd=project_dir)

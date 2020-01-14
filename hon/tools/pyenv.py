from typing import Optional

from hon.tools.setup import PyenvVersion as PyenvBase
from hon.utils import run_cmd


class Pyenv(PyenvBase):
    def create_virtualenv(self, name: str, python_version: Optional[str] = None):
        cmd = [self.executable, "virtualenv"]
        if python_version:
            self.ensure_python(python_version)
            cmd.append(python_version)
        cmd.append(name)
        run_cmd(cmd, cwd=self.cwd)

    def exec(self, cmd):
        run_cmd(
            [self.executable, "exec"] + cmd,
            env={"PYENV_VERSION": str(self.python_version)},
            cwd=self.cwd
        )

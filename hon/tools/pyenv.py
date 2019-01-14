from typing import Optional

from .setup import PyenvVersion as PyenvBase

import delegator


class Pyenv(PyenvBase):
    def create_virtualenv(self, name: str, python_version: Optional[str] = None):
        cmd = [self.executable, "virtualenv"]
        if python_version:
            self.ensure_python(python_version)
            cmd.append(python_version)
        cmd.append(name)
        delegator.run(cmd, cwd=self.cwd)

    def exec(self, cmd):
        delegator.run(
            [self.executable, "exec"] + cmd,
            env={"PYENV_VERSION": str(self.python_version)},
            cwd=self.cwd
        )

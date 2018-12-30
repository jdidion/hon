from pathlib import Path
from typing import Optional

from hon.utils import read_toml


DEFAULT_PATH = Path.home() / ".hon"
DEFAULT_CONFIG = {}


class Config:
    def __init__(self, path: Optional[Path] = None):
        if path and not path.exists():
            raise FileNotFoundError(f"Config directory {path} does not exist")

        if path is None and DEFAULT_PATH.exists():
            path = DEFAULT_PATH

        self.path = path

        if self.path:
            self._config = read_toml(self.path / "config.toml")
        else:
            self._config = DEFAULT_CONFIG

    def get_tool(self, name: str):
        return self._config.get("tools", {}).get(name, name)
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

from hon.templates import get_templates
from hon.utils import read_toml


LICENSE_URL = "https://raw.githubusercontent.com/spdx/license-list-data/master/text/{license}.txt"


class UnknownLicenseError(Exception):
    def __init__(self, license):
        super().__init__(f"License {license} not found in the SPDX repository")
        self.license = license


class Project:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.pyproject_file = project_dir / "pyproject.toml"
        if not self.pyproject_file.exists():
            raise FileNotFoundError(
                f"Hon requires a pyproject.toml file in the root of project"
                f"directory {project_dir}."
            )
        self.pyproject = read_toml(self.pyproject_file)

    def __getattr__(self, item):
        return self.get_attribute(item, required=False, section="tool.poetry")

    def get_attribute(
        self, key: str, required: bool = True, section: Optional[str] = None
    ):
        if section:
            path = section.split(".")
        else:
            path = []
        path.extend(key.split("."))
        d = self.pyproject
        for item in path:
            if not isinstance(d, dict):
                raise KeyError(f"Path {'.'.join(path)} not found in pyproject.toml")
            elif item in d:
                d = d[item]
            elif required:
                raise KeyError(f"Path {'.'.join(path)} not found in pyproject.toml")
            else:
                return None
        return d

    def create_from_templates(self):
        template_dir = get_templates()
        template_dir.create(self.project_dir, {"project": self})

    @property
    def license_text(self):
        license_file = self.project_dir / "LICENSE"
        if license_file.exists():
            with open(license_file, "rt") as inp:
                return inp.read()

        # If there is no license file, load the license text from the SPDX repo
        license = self.get_attribute("tool.poetry.license")
        license_url = LICENSE_URL.format(license=license)
        try:
            response = urlopen(license_url)
            return response.read().decode("utf-8")
        except:
            raise UnknownLicenseError(license)

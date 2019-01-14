from pathlib import Path
from typing import Optional, Sequence
from urllib.request import urlopen

from git import Repo
import delegator

from hon.templates import get_templates
from hon.utils import read_toml


LICENSE_URL = \
    "https://raw.githubusercontent.com/spdx/license-list-data/master/text/{license}.txt"


class InvalidProjectError(Exception):
    pass


class UnknownLicenseError(Exception):
    def __init__(self, license_name):
        super().__init__(f"License {license_name} not found in the SPDX repository")
        self.license_name = license_name


class Project:
    def __init__(self, root_dir: Path, git_repo: Optional[Repo] = None):
        self.root_dir = root_dir
        self._pyproject_file = root_dir / "pyproject.toml"

        if not self._pyproject_file.exists():
            raise FileNotFoundError(
                f"Hon requires a pyproject.toml file in the root of project"
                f"directory {root_dir}."
            )

        self._git_repo = git_repo
        self._pyenv = None
        self._poetry = None
        self._pyproject = None
        self._attr_cache = None

        self.refresh()

    def __getattr__(self, item):
        return self.get_attribute(item, required=False, section="tool.poetry")

    def get_attribute(
        self, key: str, required: bool = True, section: Optional[str] = None
    ):
        if key in self._attr_cache:
            return self._attr_cache[key]
        if section:
            path = section.split(".")
        else:
            path = []
        path.extend(key.split("."))
        d = self._pyproject
        for item in path:
            if not isinstance(d, dict):
                raise KeyError(f"Path {'.'.join(path)} not found in pyproject.toml")
            elif item in d:
                d = d[item]
            elif required:
                raise KeyError(f"Path {'.'.join(path)} not found in pyproject.toml")
            else:
                return None
        self._attr_cache[key] = d
        return d

    def get_dependencies(self):
        return self.get_attribute("tool.poetry.dependencies")

    def get_python_version(self):
        return self.get_attribute("tool.poetry.dependencies.python")

    @property
    def license_text(self):
        license_file = self.root_dir / "LICENSE"
        if license_file.exists():
            with open(license_file, "rt") as inp:
                return inp.read()

        # If there is no license file, load the license text from the SPDX repo
        license_name = self.get_attribute("tool.poetry.license")
        license_url = LICENSE_URL.format(license=license_name)
        try:
            response = urlopen(license_url)
            return response.read().decode("utf-8")
        except:
            raise UnknownLicenseError(license_name)

    def init(self):
        """
        Initialize the project directory.
        """
        # Create the default project files
        self.create_from_templates()

        # Add all the newly created files to the git staging area
        self.add_all_untracked()

        # Check that a compatible version of Python is available; install it if not
        self._pyenv.ensure_python(self.get_python_version())

        # Create virtualenv
        self._pyenv.create_virtualenv(self.name, self.get_python_version())

    def create_from_templates(self):
        template_dir = get_templates()
        template_dir.create(self.root_dir, {"project": self})

    def add_all_untracked(self):
        self._git_repo.index.add(self._git_repo.untracked_files)

    def refresh(self):
        self._pyproject = read_toml(self._pyproject_file)
        self._attr_cache = {}

    @property
    def pyenv(self):
        if self._pyenv is None:
            from hon.tools.pyenv import Pyenv
            self._pyenv = Pyenv(
                working_dir=self.root_dir, python_version=self.get_python_version()
            )
        return self._pyenv

    @property
    def poetry(self):
        if self._poetry is None:
            from hon.tools.poetry import Poetry
            self._poetry = Poetry()
        return self._poetry

    @property
    def git(self):
        if self._git_repo is None:
            from git.repo.fun import is_git_dir
            if not is_git_dir(self.root_dir):
                raise InvalidProjectError(
                    f"Project directory {self.root_dir} is not a git repository"
                )
            self._git_repo = Repo(self.root_dir)
        return self._git_repo

    def build(self, install: bool = False, **kwargs):
        self.poetry.build(**kwargs)
        if install:
            self.install()

    @property
    def wheel(self):
        abi = "none"
        platform = "any"
        version = f"py{self.get_python_version()[0]}"
        return self.root_dir / "dist" / \
            f"{self.name}-{self.version}-{version}-{abi}-{platform}.whl"

    def install(self):
        self.pyenv.exec(["pip", "install", "--upgrade", self.wheel])

    def uninstall(self, name: Optional[str] = None):
        if name is None:
            name = self.name
        self.pyenv.exec(["pip", "uninstall", "-y", name])

    def add_dependency(
        self, name: Optional[str] = None, exact: bool = False, dev: bool = False,
        optional: bool = False
    ):
        pkg = None

        if name:
            pkg = self.poetry.add(name, dev, optional)
            if not pkg and exact:
                raise CommandError(f"Could not find dependency {name}")

        if pkg is None:
            name = self.poetry.search(name)
            if name:
                self.poetry.add(name, dev, optional)
            else:
                return

        if pkg:
            self.update_dependencies()

    def remove_dependency(self, name: str, dev: bool = False):
        pkg = self.poetry.remove(name, dev)
        self.uninstall(pkg)
        self.lock_dependencies()

    def update_dependencies(self, dev: bool = True):
        self.poetry.update(dev=dev)
        self.lock_dependencies()

    def lock_dependencies(self):
        self.poetry.lock()

    def test(self, tests: Optional[Sequence[str]] = None, debug: bool = False):
        cmd = ["pytest", "--cov", "--cov-report", "term-missing"]
        if debug:
            cmd.extend(["-s", "-vv", "--full-trace"])
        else:
            cmd.append("--show-capture=all")
        if tests:
            cmd.extend(tests)
        delegator.run(cmd)

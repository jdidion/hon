#!/usr/bin/env python
"""
Install Hon and all its prerequisites and dependencies. Even though Hon requires
Python 3.6+, this script is compatible with Python 2, as it installs Pyenv (if it's
not already installed), uses Pyenv to install a compatible Python, then installs
Pipsi, and finally uses Pipsi to install Hon.
"""
from argparse import ArgumentParser
import operator
import os
import re
import subprocess
import sys


# Version Parsing

VERSION_RE = re.compile(r"\*?\s*([^\s]+).*")
CONSTRAINT_RE = re.compile(r"^([><!=]*)(.*)$")
OPERATORS = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne
}


class PythonVersion:
    def __init__(self, major, minor, patch, is_prerelease):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.is_prerelease = is_prerelease

    @staticmethod
    def parse(version, allow_prerelease=True):
        if not version[0].isdigit():
            return None
        is_prerelease = False
        if version.endswith("-dev"):
            if not allow_prerelease:
                return None
            is_prerelease = True
            version = version[:-4]
        version = version.split(".")
        if len(version) < 3:
            version.extend([0] * (3 - len(version)))
        return PythonVersion(*(int(v) for v in version), is_prerelease=is_prerelease)

    def bump(self, which, keep_prerelease=False):
        newver, is_prerelease = self.as_tuple()
        if which == "major":
            newver[0] += 1
        elif which == "minor":
            newver[1] += 1
        else:
            newver[2] += 1
        if not keep_prerelease:
            is_prerelease = False
        return PythonVersion(*newver, is_prerelease)

    def as_tuple(self):
        return [self.major, self.minor, self.patch], self.is_prerelease

    def __str__(self):
        version, is_prerelease = self.as_tuple()
        version = ".".join(str(v) for v in version)
        if is_prerelease:
            version += "-dev"
        return version


def run(cmd, echo=True, **kwargs):
    if echo:
        if "stdin" not in kwargs:
            kwargs["stdin"] = sys.stdin
        if "stdout" not in kwargs:
            kwargs["stdout"] = sys.stdout
        if "stderr" not in kwargs:
            kwargs["stderr"] = sys.stderr
    return subprocess.run(cmd, **kwargs)


def run_pipe(cmd, pipe_cmd, cwd=None, pipe_env=None):
    proc1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=cwd)
    proc2 = subprocess.Popen(
        pipe_cmd, stdin=proc1.stdout, stdout=sys.stdout, env=pipe_env, cwd=cwd
    )
    proc1.stdout.close()
    proc2.wait()


def constraints_allow(constraints, version):
    for op, cmp_version in constraints:
        if not (op(version, cmp_version)):
            return False
    return True


def parse_constraints(constraints):
    expanded = []
    for constraint in constraints.split(","):
        if constraint.startswith("^"):
            ver = PythonVersion.parse(constraint[1:])
            expanded.append((operator.ge, ver))
            expanded.append((operator.lt, ver.bump("major")))
        elif constraint.startswith("~"):
            ver = PythonVersion.parse(constraint[1:])
            expanded.append((operator.ge, ver))
            expanded.append((operator.lt, ver.bump("minor")))
        elif constraint.endswith("*"):
            ver = PythonVersion.parse(constraint[:-1])
            expanded.append((operator.ge, ver))
            if constraint.count(".") == 1:
                expanded.append((operator.lt, ver.bump("major")))
            else:
                expanded.append((operator.lt, ver.bump("minor")))
        else:
            m = CONSTRAINT_RE.match(constraint)
            if not m:
                raise ValueError("Invalid constraint: {}".format(constraint))
            op, version = m.groups()
            if op not in OPERATORS:
                raise ValueError("Invalid operator: {}".format(operator))
            expanded.append((OPERATORS[op], PythonVersion.parse(version)))
    return expanded


def get_installed_python_versions(prerelease=None):
    return list(filter(
        None, (
            PythonVersion.parse(
                VERSION_RE.match(version).group(1), prerelease is not False
            )
            for version in run(["pyenv", "versions"]).stdout.splitlines()
        )
    ))


def get_available_python_versions(prerelease):
    lines = run(["pyenv", "install", "--list"]).stdout.splitlines()
    assert lines[0] == "Available versions:"
    return list(filter(
        None, (PythonVersion.parse(v.strip(), prerelease is True) for v in lines[1:])
    ))


def select_python_version(constraints, versions):
    constraints = parse_constraints(constraints)
    for version in sorted(versions, reverse=True):
        if constraints_allow(constraints, version):
            return version


# pyenv

class Pyenv:
    def __init__(self, executable=None, root_dir=None, working_dir=None):
        self.executable = str(executable) if executable else "pyenv"
        self.root = root_dir or os.path.expanduser("~/.pyenv")
        self.cwd = str(working_dir or os.getcwd())

    @classmethod
    def install(cls):
        run_pipe(["curl", "-L", PYENV_URL], ["bash"])
        return cls()

    def ensure_plugin(self, url, name=None):
        plugins = os.path.join(self.root, "plugins")
        if not os.path.exists(plugins):
            os.mkdir(plugins)
        if name is None:
            name = url.split("/")[-1]
            if name.endswith(".git"):
                name = name[:-4]
        plugin_dir = os.path.join(plugins, name)
        if not os.path.exists(plugin_dir):
            run(["git", "clone", url, str(plugin_dir)])

    def ensure_python(self, version, allow_prerelease=True):
        installed = get_installed_python_versions(allow_prerelease)
        python_version = select_python_version(version, installed)
        if python_version is None:
            available = get_available_python_versions(allow_prerelease)
            python_version = select_python_version(version, available)
            self.install_python(python_version)
        return python_version

    def install_python(self, version):
        run([self.executable, "install", str(version)])


class PyenvVersion(Pyenv):
    def __init__(
        self, executable=None, root_dir=None, working_dir=None, python_version=None
    ):
        super(PyenvVersion, self).__init__(executable, root_dir, working_dir)
        version_file = os.path.join(self.cwd, ".python-version")
        if python_version is None and os.path.exists(version_file):
            with open(version_file) as inp:
                python_version = inp.read().strip()
        self.python_version = python_version

    def ensure_python(self, version, allow_prerelease=True):
        version = super().ensure_python(version, allow_prerelease)
        if self.python_version is None:
            self.python_version = version
        return version

    def pipe_to_python(self, cmd):
        run_pipe(
            cmd, [self.executable, "exec", "python"],
            pipe_env={"PYENV_VERSION": str(self.python_version)},
            cwd=self.cwd
        )

    def get_bin(self, executable="python"):
        return os.path.join(
            self.root, "versions", str(self.python_version), "bin", executable
        )


# Ideally, the below would be in a separate script that imports a module with the
# above functions, but in order to provide a single installation script it is best
# to combine them in the same file.


PYTHON_CONSTRAINT = "^3.6"
PYENV_URL = "https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer"
PYENV_VIRTUALENV_URL = "https://github.com/pyenv/pyenv-virtualenv.git"
PIPSI_URL = "https://raw.githubusercontent.com/mitsuhiko/pipsi/master/get-pipsi.py"
TOOLS = {
    "hon": "*",
    "black": "*",
    "flake8": "^3.6.0",
    "poetry": ">=0.12",
    "pytest": ("^3.0", {
        "pytest-cov": "^2.4"
    }),
    "sphinx": ("^1.8.3", {
        "napoleon": "^1.3",
        "recommonmark": "^0.4.0"
    })
}


def is_installed(cmd):
    return run(["command", "-v", cmd]).returncode == 0


def get_dependency(name, constraint="*"):
    if constraint == "*":
        return name
    else:
        return "{}{}".format(name, constraint)


def install_tool(name, constraints, deps=None, python=None):
    cmd = ["pipsi", "install"]
    if python:
        cmd.extend(["--python", python])
    cmd.append(get_dependency(name, constraints))
    run(cmd)
    if deps:
        pip = os.path.join(os.path.expanduser("~.local"), "venvs", name, "bin", "pip")
        for pkg, pkg_constraint in deps.items():
            run([pip, "install", get_dependency(pkg, pkg_constraint)])


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--prerelease", action="store_true", dest="prerelease",
        help="Allow pre-release versions"
    )
    parser.add_argument(
        "--no-prerelease", action="store_false", dest="prerelease",
        help="Do not allow pre-release versions"
    )
    parser.add_argument("version", help="Version constraint")
    args = parser.parse_args()

    # Ensure pyenv is installed
    if is_installed("pyenv"):
        pyenv = PyenvVersion()
    else:
        pyenv = PyenvVersion.install()

    # Ensure pyenv-virtualenv is installed
    pyenv.ensure_plugin(PYENV_VIRTUALENV_URL)

    # Ensure pyenv has a compatible version of python available
    pyenv.ensure_python(PYTHON_CONSTRAINT, args.prerelease)

    # Ensure pipsi is installed
    if not is_installed("pipsi"):
        pyenv.pipe_to_python(["curl", "-L", PIPSI_URL])

    # Resolve the python executable to use when installing tools with pipsi
    python = pyenv.get_bin()

    # Install the tools
    for name, constraints in TOOLS.items():
        deps = None
        if isinstance(constraints, tuple):
            constraints, deps = constraints
        install_tool(name, constraints, deps, python)

    # Disable automatic creation of virtualenvs by poetry
    run(["poetry", "config", "settings.virtualenvs.create", "false"])


if __name__ == "__main__":
    main()

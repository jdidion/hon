![logo](docs/assets/logo.png)

**Hon is currently in development. Not all of the functionality described here is yet available.**

Hon is an opinionated project management tool. It strives to automate the mundane tasks of building, testing, and publishing python packages, freeing you to focus on the code.

Hon bundles together a specific set of tools and relies upon a particular project organization. The best way to use Hon is to let it create your project for you, but it can also manage your existing projects if you follow the rules.

Hon is not for everyone. It is minimally configurable and has relatively few options. If you are a developer who likes everything about your project setup to be *just so*, you will probably get frustrated with Hon. However, if you are willing to sacrifice flexibility for productivity, Hon will make your life as a developer much easier.

## Requirements

Hon requires Python 3.6+.

The following tools are required to be installed. We suggest using [pipsi]() to perform the installation. The provided [setup](tools/setup_tools.sh) script will install all of these tools for you.

* [Poetry]() >= 0.12: dependency and build management
* [pyenv](https://github.com/pyenv/pyenv): install and manage your python versions.
    * [pyenv-virtualenv](): Use virtual environments with pyenv
* [Pytest](): unit testing
    * [pytest-cov]() plugin for coverage
* [Black](): code formatter
* [Flake8](): linting
* [MyPy](): static type checking
* [Sphinx](): documentation
    * recommonmark
    * napoleon

## Installation

Hon can be installed from PyPI using pip.

```bash
$ pip install hon
```

## Commands

### Project creation

The `create` command creates a new project with the following layout:

```
{name}
|_{name}
| |_ __init__.py
| |_ __version__.py
|_docs
|_tests
| |_ __init__.py
| |_ test_{name}.py
|_.gitignore
|_CHANGES
|_LICENSE
|_pyproject.toml
|_README.md
```

Additional files can also be created, and the contents of these files can be modified to some degree using recipes (see [Configuration](##Configuration)).

Creating the [pyproject.toml](PEP518) file requires some metadata. The only required information is the project name, but other items such as description, version, and dependencies can either be specified on the command line or interactively.

If you have [pyenv]() installed and no currently installed Python version satisfies the version specified in pyproject.toml, an appropriate version will be insalled for you.

By default, the project is initiated as a git repository and all the newly created files are added to the staging area.

Finally, a virtualenv is created for the project.

### Configuration

Hon does not require configuration, but if you want you can store some defaults and also customize the templates used when creating a new project.

Hon looks for configuration in `$HOME/.hon/`. Within this folder, it looks for a `config.toml` file:

Hon also looks for a `templates/` subfolder. Wihin this folder, you can define any number of recipes, any of which can be used to bootstrap a new project. In addition, you can put common templates in `templates/default/`. Hon resolves the set of templates that will be used to create a new project in the following order:

`$HOME/.hon/templates/{recipe} > $HOME/.hon/templates/default > packaged templates`.

A recipe mirrors the project directory structure. You only need to provide the files that you want to override from a higher level. Recipes are always additive - there is no way to exlude templates defined at a higher level.

### Project build

The `build` command builds both a wheel and a source distribution into the `dist` folder.

The `install` command installs a build into the project's virtualenv (this can also be done using the `--install` option of the `build` command). Any dependencies are also installed.

### Dependencies

Hon largely wraps the dependency management functionality provided by Poetry. The `dep` command has the following subcommands:

* `add`: Add a dependency to the pyproject.toml and install it into the virtualenv
* `remove`: Remove a dependency to the pyproject.toml and remove it from the virtualenv
* `update`: Update dependencies within the constraints of their version specifications

These commands also update the lock file (`poetry.lock`), which sets the exact version for each dependency. The lock file can also be manually (re)created using the `lock` subcommand.

### Code hygine

The `format` command formats your source files using [black]().

The `lint` command runs the [flake8]() linter. Identified issues are sorted by file and then by line number. The report can be opened in your editor rather than printing to stdout.

The `types` command runs [MyPy](), which performs static type checking. This is only valid for python 3.5+ projects.

The `test` command runs your unit tests and generates a coverage report. Tests are run in the virtualenv by default. If necessary, dependencies are installed prior to running tests.

### Versioning

The canonical version of your software is in the pyproject.toml file. The `version` command uses the [Poetry `version` command]() to increase the version. Note that Poetry enforces conformance to [PEP440](https://www.python.org/dev/peps/pep-0440), which in some cases is at odds with the original definition of Semantic Versioning.

To solve the common use case of needing to access the current version from within your program, Hon creates a `__version__.py` file in your source directory and keeps it in sync with the version in pyproject.toml. Thus, from within your code, you can access the version as follows:

```python
from {mypackage}.__version__ import version
```

Bumping the version will also update your CHANGES file as described below.

### Source control

The `commit` command is `git commit` on steroids. First, any changed files are reformatted (using the `format` command). Next, unless `--force` is specified, the `lint`, `build`, `install`, and `test` commands are run. Finally, the changes are committed to the local git repository.

By default, the commit message is used to add a change to the CHANGES file. This works as follows:

* The first line of the commit message (ending with "\n") is used as change description.
* The commit ID is added in parentheses at the end of the change line.
* Any bullet points (beginning with '*') immediately after the first line of the commit message are added as sub-points under the change line.
* Any additional content in the commit message is not added to CHANGES.

The following options are available:

* --add Add all untracked files
* --push Push to the remote after commit
* --no-change: Do not add this commit message as an entry in the change list

We should note that git already has a mechanism for performing arbitrary tasks prior to commit, called pre-commit hooks, which is orthogonal to, but completely compatible with, Hon. If you'd like to take advantage of this, we recommend the [pre-commit](https://github.com/pre-commit/pre-commit) framework.

### Changes

Hon manages your CHANGES list for you. Changes can be added automatically when committing code using `commit`. The `change` command can also add an entry for you. Entries are always added to the current (top-most) block.

A changes block starts out having the title "Unreleased." When the version is bumped, if the top-most block is named "Unreleased," the title is changed to the version. If a release is performed, the release date is added in parentheses to the title of the top-most block (along with any tags you specify), and a new "Unreleased" block is created (unless the `--bump` option is specified). A new block is also created if the version is bumped without doing a release.

### Releasing and publishing

The `release` command creates an official release of your software on GitHub. A release is performed as follows:

* Ensure that the version has been increased since the last release. You cannot make two releases with the same version.
* If there are any uncommitted files, run the `commit` command (`format`, `lint`, `build`, `install`, `test`, and `git commit`)
* `git push --dry-run`, to test whether a push will succeed. If there are any merge conflicts, you'll need to resolve them and try again.
* Add a tag for the current version using `git tag`
* `git push`
* Create a release and upload all assets

Publishing is the act of uploading a release to a repository such as PyPI (the default) or Conda. The `publish` command uses credential information stored in `.pypirc` or in the Hon `config.toml` file to authenticate with the remote repository.

Hon can publish to either the main Conda repository (using the Conda command line client) or to a GitHub-based repository such as Bioconda.

Hon can also publish a Docker image for your python command line application. You may place a Dockerfile in your project directory, or you can have Hon build you one using a default base image. The CMD directive is determined as follows:

* `--cmd` option specified on the command line
* The first entry point (if any) in pyproject.toml
* The \_\_main\_\_.py module, if any

### Documentation

The `docs` command builds the project documentation and opens the index file in your browser.

### Virtual environments

 The following commands manage virtual environments:

* `refresh`: delete and recreate a virtualenv
* `run`: run a command in a virtualenv

We suggest following the [instructions](https://github.com/pyenv/pyenv-virtualenv) to add `pyenv virtualenv-init` to your
shell. This will automatically activate the virtualenv for a project when you `cd` into that project's directory, and deactivate it when you cd out.

### Project cleanup

The `clean` command deletes transient files in your project directory. By default, this includes all files that match any patterns in the .gitignore file. You can also delete files that are not tracked by git using the `--untracked` option. You can specify additional patterns to clean in the [config.toml](###Configuration) file.

Unless the `--force` option is specified, a paginated list of files to be deleted is shown and confirmation is required to delete the files.

## Example Hon workflow

1. Create a new project using `hon create`.
2. Add and modify test and source files (ideally in that order, using test-driven development).
3. Periodically run tests using `hon test` and fix any failures.
3. Commit changes using `hon commit`. Strive for many small commits. Ideally, each commit should encompass a single, byte-sized chunk of work, such as fixing a bug or implementing a sub-task of a user story.
4. Create a release using `hon release`.
5. Optionally, publish the release to one or more repositories.
6. Continue development. You can bump the version at release time, or do it sometime later (using `hon version`).

## FAQ

### Wheredja get dat name, hon?

Hon pays homage to the people of Baltimore, who are known for being both hard-working and opinionated. Hon is also short for "honey do," as in a list of tasks you ask your favorite project manager to take care of for you. It's also a nice coincidence that Python ends with "hon."

### An wheredja get dat art?

I found it using Google Image Search, and despite my best efforts have been unable to trace it back to its creator. If it's your work, please get in touch; I'm happy to attribute it to you, or to stop using it if you wish (though I hope you don't because I love it).

### Why did you choose these specific tools?

I've tried lots of developer tools - these are the best. If you disagree, feel free to complain about it on HackerNews. 😊

### Will you support my favorite tool?

Maybe, but probably not. If you haven't already gotten the picture, Hon is unashamedly opinionated. Simplicity and flexibility are usually at odds, and Hon is all about simplicity. That said, feel free to request support for a tool by creating a GitHub issue. You are, of course, also welcome to fork Hon and modify it as you wish.

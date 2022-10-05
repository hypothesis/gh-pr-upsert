<a href="https://github.com/hypothesis/gh-pr-upsert/actions/workflows/ci.yml?query=branch%3Amain"><img src="https://img.shields.io/github/workflow/status/hypothesis/gh-pr-upsert/CI/main"></a>
<a href="https://pypi.org/project/gh-pr-upsert"><img src="https://img.shields.io/pypi/v/gh-pr-upsert"></a>
<a><img src="https://img.shields.io/badge/python-3.10 | 3.9 | 3.8-success"></a>
<a href="https://github.com/hypothesis/gh-pr-upsert/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-BSD--2--Clause-success"></a>
<a href="https://github.com/hypothesis/cookiecutters/tree/main/pypackage"><img src="https://img.shields.io/badge/cookiecutter-pypackage-success"></a>
<a href="https://black.readthedocs.io/en/stable/"><img src="https://img.shields.io/badge/code%20style-black-000000"></a>

# gh-pr-upsert

A GitHub CLI extension to upsert pull requests.
The `gh pr-upsert` command will create a new pull request (PR) with the commits
on your current branch, generating a PR title and body from your commit
messages:

```terminal
$ gh pr-upsert
There's no PR for this branch yet, creating one
```

Unlike `gh pr create`, `gh pr-upsert` always pushes your branch directly to the
GitHub repo before opening a PR. It's a non-interactive command and doesn't ask
you whether or not to push or offer to create a fork.

Also unlike `gh pr create`, if there's already a PR for the branch then `gh
pr-upsert` will force push it:

```terminal
$ gh pr-upsert
There's already an open PR for this branch
Your local changes are different from the open PR
No one else has pushed to the PR, updating it
```

Requires [Git](https://git-scm.com/) and [GitHub CLI](https://cli.github.com/)
to be installed.

To install the latest version of `gh-pr-upsert` as a GitHub CLI extension run:

```terminal
gh extension install hypothesis/gh-pr-upsert
```

Then to upgrade to a new version run `gh extension upgrade gh-pr-upsert`.
To remove the extension run `gh extension remove gh-pr-upsert`.

Alternatively you can install `gh-pr-upsert` as a Python package and the
command will be `gh-pr-upsert` rather than `gh pr-upsert`. See below for
details.

## Installing

We recommend using [pipx](https://pypa.github.io/pipx/) to install
gh-pr-upsert.
First [install pipx](https://pypa.github.io/pipx/#install-pipx) then run:

```terminal
pipx install gh-pr-upsert
```

You now have gh-pr-upsert installed! For some help run:

```
gh-pr-upsert --help
```

## Upgrading

To upgrade to the latest version run:

```terminal
pipx upgrade gh-pr-upsert
```

To see what version you have run:

```terminal
gh-pr-upsert --version
```

## Uninstalling

To uninstall run:

```
pipx uninstall gh-pr-upsert
```

## Setting up Your gh-pr-upsert Development Environment

First you'll need to install:

* [Git](https://git-scm.com/).
  On Ubuntu: `sudo apt install git`, on macOS: `brew install git`.
* [GNU Make](https://www.gnu.org/software/make/).
  This is probably already installed, run `make --version` to check.
* [pyenv](https://github.com/pyenv/pyenv).
  Follow the instructions in pyenv's README to install it.
  The **Homebrew** method works best on macOS.
  The **Basic GitHub Checkout** method works best on Ubuntu.
  You _don't_ need to set up pyenv's shell integration ("shims"), you can
  [use pyenv without shims](https://github.com/pyenv/pyenv#using-pyenv-without-shims).

Then to set up your development environment:

```terminal
git clone https://github.com/hypothesis/gh-pr-upsert.git
cd gh-pr-upsert
make help
```

## Releasing a New Version of the Project

1. First, to get PyPI publishing working you need to go to:
   <https://github.com/organizations/hypothesis/settings/secrets/actions/PYPI_TOKEN>
   and add gh-pr-upsert to the `PYPI_TOKEN` secret's selected
   repositories.

2. Now that the gh-pr-upsert project has access to the `PYPI_TOKEN` secret
   you can release a new version by just [creating a new GitHub release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).
   Publishing a new GitHub release will automatically trigger
   [a GitHub Actions workflow](.github/workflows/pypi.yml)
   that will build the new version of your Python package and upload it to
   <https://pypi.org/project/gh-pr-upsert>.

## Changing the Project's Python Versions

To change what versions of Python the project uses:

1. Change the Python versions in the
   [cookiecutter.json](.cookiecutter/cookiecutter.json) file. For example:

   ```json
   "python_versions": "3.10.4, 3.9.12",
   ```

2. Re-run the cookiecutter template:

   ```terminal
   make template
   ```

3. Commit everything to git and send a pull request

## Changing the Project's Python Dependencies

To change the production dependencies in the `setup.cfg` file:

1. Change the dependencies in the [`.cookiecutter/includes/setuptools/install_requires`](.cookiecutter/includes/setuptools/install_requires) file.
   If this file doesn't exist yet create it and add some dependencies to it.
   For example:

   ```
   pyramid
   sqlalchemy
   celery
   ```

2. Re-run the cookiecutter template:

   ```terminal
   make template
   ```

3. Commit everything to git and send a pull request

To change the project's formatting, linting and test dependencies:

1. Change the dependencies in the [`.cookiecutter/includes/tox/deps`](.cookiecutter/includes/tox/deps) file.
   If this file doesn't exist yet create it and add some dependencies to it.
   Use tox's [factor-conditional settings](https://tox.wiki/en/latest/config.html#factors-and-factor-conditional-settings)
   to limit which environment(s) each dependency is used in.
   For example:

   ```
   lint: flake8,
   format: autopep8,
   lint,tests: pytest-faker,
   ```

2. Re-run the cookiecutter template:

   ```terminal
   make template
   ```

3. Commit everything to git and send a pull request

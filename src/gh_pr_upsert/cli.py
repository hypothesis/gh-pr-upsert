import sys
from argparse import ArgumentParser
from importlib.metadata import version
from subprocess import CalledProcessError

from gh_pr_upsert import core
from gh_pr_upsert.core import PRUpsertError


def cli(_argv=None):
    parser = ArgumentParser(
        prog="gh pr-upsert",
        description="Create or update a pull request for the current branch.",
    )
    parser.add_argument("-v", "--version", action="store_true")

    args = parser.parse_args(_argv)

    if args.version:
        print(version("gh-pr-upsert"))
        sys.exit()

    try:
        core.pr_upsert()
    except PRUpsertError as err:
        print(err.message)
        sys.exit(err.exit_status)
    except CalledProcessError as err:
        if err.stderr:
            print(err.stderr.decode("utf-8"))
        if err.stdout:
            print(err.stdout.decode("utf-8"))
        raise

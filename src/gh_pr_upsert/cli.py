import sys
from argparse import ArgumentParser
from importlib.metadata import version
from subprocess import CalledProcessError

from gh_pr_upsert import core
from gh_pr_upsert.core import PRUpsertError
from gh_pr_upsert.git import GitHubRepo, current_branch, fetch_url


def cli(_argv=None):
    parser = ArgumentParser(
        description="Create or update a GitHub pull request for the current branch into the default branch."
    )
    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument(
        "--base",
        help="the git remote to use for the base of the pull request (default: 'origin')",
        default="origin",
    )
    parser.add_argument(
        "--head",
        help="the git remote to use for the head of the pull request (default: 'origin')",
        default="origin",
    )
    parser.add_argument(
        "--title",
        help="the title to use when creating new pull requests",
        default="Automated changes by gh-pr-upsert",
    )
    parser.add_argument(
        "--body",
        help="the body to use when creating new pull requests",
        default="Automated changes by [gh-pr-upsert](https://github.com/hypothesis/gh-pr-upsert).",
    )
    parser.add_argument(
        "--body-file",
        help="path to a file containing the body text to use when creating new pull requests",
    )
    parser.add_argument(
        "--close-comment",
        help="the comment to leave on PRs when closing them",
        default="It looks like this PR isn't needed anymore, closing it.",
    )

    args = parser.parse_args(_argv)

    if args.version:
        print(version("gh-pr-upsert"))
        sys.exit()

    # FIXME: Just pass through body_file directly to `gh pr create`.
    if args.body_file is not None:
        # --body-file overrides --body if both are given at once.
        with open(args.body_file, "r") as body_file:
            args.body = body_file.read()

    if args.body is None:
        args.body = "Automated changes by [gh-pr-upsert](https://github.com/hypothesis/gh-pr-upsert)."

    try:
        core.pr_upsert(args.base, args.head, args.title, args.body)
    except PRUpsertError as err:
        print(err.message)
        sys.exit(err.exit_status)
    except CalledProcessError as err:
        if err.stderr:
            print(err.stderr.decode("utf-8"))
        if err.stdout:
            print(err.stdout.decode("utf-8"))
        raise

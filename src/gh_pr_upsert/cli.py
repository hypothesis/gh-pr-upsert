import sys
from argparse import ArgumentParser
from importlib.metadata import version
from subprocess import CalledProcessError

from gh_pr_upsert import core, git
from gh_pr_upsert.exceptions import PRUpsertError


def cli(_argv=None):  # pylint:disable=too-complex
    parser = ArgumentParser(description="Create or update a GitHub pull request.")
    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument(
        "--base-remote",
        help="the git remote to use for the base of the pull request (default: 'origin')",
        default="origin",
    )
    parser.add_argument(
        "--base-branch",
        help="the git branch to use for the base of the pull request (default: --base-remote's default branch)",
    )
    parser.add_argument(
        "--local-branch",
        help="the local git branch to push (default: the current branch)",
    )
    parser.add_argument(
        "--head-remote",
        help="the git remote to use for the head of the pull request (default: 'origin')",
        default="origin",
    )
    parser.add_argument(
        "--head-branch",
        help="the git branch to use for the head of the pull request (default: the branch on --head-remote with same name as --local-branch)",
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

    base_repo = git.GitHubRepo.get(args.base_remote)
    head_repo = git.GitHubRepo.get(args.head_remote)

    if args.base_branch is None:
        args.base_branch = base_repo.default_branch

    if args.local_branch is None:
        args.local_branch = git.current_branch()

    if args.head_branch is None:
        args.head_branch = args.local_branch

    if args.body_file is not None:  # pragma: no cover
        # --body-file overrides --body if both are given at once.
        with open(args.body_file, "r", encoding="utf-8") as body_file:
            args.body = body_file.read()

    try:
        core.pr_upsert(
            base_repo,
            args.base_branch,
            args.local_branch,
            head_repo,
            args.head_branch,
            args.title,
            args.body,
            args.close_comment,
        )
    except PRUpsertError as err:
        print(err.message)
        sys.exit(err.exit_status)
    except CalledProcessError as err:
        if err.stderr:
            print(err.stderr.decode("utf-8"))
        if err.stdout:
            print(err.stdout.decode("utf-8"))
        raise

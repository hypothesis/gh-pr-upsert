"""Helpers for working with Git and GitHub."""
from dataclasses import dataclass, field
from functools import cache
from subprocess import CalledProcessError
from typing import Optional

from gh_pr_upsert.exceptions import OtherPeopleError
from gh_pr_upsert.run import run


@dataclass(frozen=True)
class User:
    name: str
    email: str


@dataclass(frozen=True)
class Commit:
    sha: str
    author: User

    @classmethod
    def get(cls, sha: str):
        def git_show(format_string: str) -> str:
            return run(["git", "show", "--no-patch", f"--format={format_string}", sha])

        # `git show` doesn't have a machine-readable output mode (like a --json
        # mode) and I don't fancy writing code to parse its human-readable
        # output. So call `git show` multiple times with a different --format
        # string each time to extract the different attributes of the commit.
        return cls(
            sha=git_show("%H"),  # Call git to make sure we get the full SHA.
            author=User(
                name=git_show("%an"),
                email=git_show("%ae"),
            ),
        )


@dataclass(frozen=True)
class GitHubRepo:
    owner: str
    name: str
    name_with_owner: str
    default_branch: str = field(repr=False, compare=False)
    url: str = field(repr=False, compare=False)
    json: Optional[dict] = field(repr=False, compare=False)

    @classmethod
    def get(cls, remote: str):
        json = run(
            [
                "gh",
                "repo",
                "view",
                "--json",
                "owner,name,nameWithOwner,defaultBranchRef,url",
                run(["git", "remote", "get-url", remote]),
            ],
            json=True,
        )

        return cls(
            owner=json["owner"]["login"],
            name=json["name"],
            name_with_owner=json["nameWithOwner"],
            default_branch=json["defaultBranchRef"]["name"],
            url=json["url"],
            json=json,
        )


@dataclass(frozen=True)
class PullRequest:
    base_repo: GitHubRepo
    head_repo: GitHubRepo
    head_branch: str
    number: int
    url: str = field(compare=False, repr=False)
    json: Optional[dict] = field(compare=False, repr=False)

    @classmethod
    def get(cls, base_repo, head_repo, head_branch):
        # We can't use `gh pr view` to get a PR from GitHub because the error
        # that happens when there's no matching PR and we should return None
        # isn't distinguishable from other errors that should cause us to crash
        # (there are no machine-readable error codes).
        #
        # We can't use `gh pr list` to find a matching PR because it only
        # returns the most recent 30 PRs.
        #
        # So we call the list pull requests API
        # (https://docs.github.com/en/rest/pulls/pulls#list-pull-requests)
        # with pagination. I think this should search all open PRs.
        #
        # For how to call the GitHub API through GitHub CLI see:
        # https://cli.github.com/manual/gh_api
        # (it handles authentication and pagination for us).

        matching_prs = run(
            [
                "gh",
                "api",
                "--paginate",
                "--method",
                "GET",
                f"/repos/{base_repo.owner}/{base_repo.name}/pulls",
                "-f",
                f"base={base_repo.default_branch}",
                "-f",
                f"head={head_repo.owner}:{head_branch}",
                "-f",
                "state=open",
            ],
            json=True,
        )

        if not matching_prs:
            return None

        assert len(matching_prs) == 1

        json = matching_prs[0]

        return PullRequest(
            base_repo=base_repo,
            head_repo=head_repo,
            head_branch=head_branch,
            number=json["number"],
            url=json["url"],
            json=json,
        )

    def close(self, comment) -> None:
        run(
            [
                "gh",
                "pr",
                "close",
                "--repo",
                self.base_repo.name_with_owner,
                "--delete-branch",
                "--comment",
                comment,
                str(self.number),
            ]
        )


def branch_exists(remote: str, branch: str) -> bool:
    """Return True if `remote` has a branch named `branch`."""
    try:
        run(["git", "show-ref", f"refs/remotes/{remote}/{branch}"])
    except CalledProcessError as err:
        if err.returncode == 1:
            return False
        raise

    return True


def configured_user():
    """Return the configured git user."""
    return User(
        name=run(["git", "config", "--get", "user.name"]),
        email=run(["git", "config", "--get", "user.email"]),
    )


def contributors(branches: list[str]) -> list[User]:
    """Return the list of users who've contributed to the given branches."""
    return set([commit.author for commit in log(branches)])


def current_branch() -> str:
    """Return the name of the current local git branch."""
    return run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"])


def diff(branches: list[str]) -> str:
    """Return the output of `git diff <branch>...` for the given `branches`."""
    return run(["git", "diff", *branches])


def log(branches: list[str]) -> list[Commit]:
    """Return the commits from `git log <branch>...` for the given `branches`."""
    return [
        Commit.get(sha)
        for sha in run(
            ["git", "log", "--ignore-missing", *branches, "--format=%H"]
        ).split()
    ]


def push(remote: str, branch: str) -> None:
    """Force-push <branch> to <remote>/<branch>."""
    run(["git", "push", "--force-with-lease", remote, f"{branch}:{branch}"])

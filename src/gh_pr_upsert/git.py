"""Helpers for working with Git and GitHub."""

from dataclasses import dataclass, field
from functools import cache
from subprocess import CalledProcessError
from typing import Optional

from gh_pr_upsert.run import run


@dataclass(frozen=True)
class User:
    name: str
    email: str


@dataclass(frozen=True)
class Commit:
    sha: str
    author: User
    committer: User

    @classmethod
    @cache
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
            committer=User(
                name=git_show("%cn"),
                email=git_show("%ce"),
            ),
        )


@dataclass(frozen=True)
class GitHubRepo:
    remote: str
    owner: str
    name: str
    name_with_owner: str = field(repr=False, compare=False)
    default_branch: str = field(repr=False, compare=False)
    url: str = field(repr=False, compare=False)
    json: Optional[dict] = field(repr=False, compare=False)

    @classmethod
    @cache
    def get(cls, remote: str):
        remote_url = run(["git", "remote", "get-url", remote])

        json = run(
            [
                "gh",
                "repo",
                "view",
                "--json",
                "owner,name,nameWithOwner,defaultBranchRef,url",
                remote_url,
            ],
            json=True,
        )

        return cls(
            remote=remote,
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
    html_url: str = field(compare=False, repr=False)
    json: Optional[dict] = field(compare=False, repr=False)

    @classmethod
    def from_json(cls, base_repo, head_repo, head_branch, json):
        """Return a PullRequest from the given GitHub API JSON data."""
        return cls(
            base_repo=base_repo,
            head_repo=head_repo,
            head_branch=head_branch,
            number=json["number"],
            html_url=json["html_url"],
            json=json,
        )

    @classmethod
    def create(
        cls, base_repo, base_branch, head_repo, head_branch, title, body
    ):  # pylint: disable=too-many-arguments,too-many-positional-arguments
        json = run(
            [
                "gh",
                "api",
                "--header",
                "X-GitHub-Api-Version:2022-11-28",
                "--method",
                "POST",
                f"/repos/{base_repo.owner}/{base_repo.name}/pulls",
                "-f",
                f"base={base_branch}",
                "-f",
                f"head={head_repo.owner}:{head_branch}",
                "-f",
                f"title={title}",
                "-f",
                f"body={body}",
            ],
            json=True,
        )

        return cls.from_json(base_repo, head_repo, head_branch, json)

    @classmethod
    @cache
    def get(cls, base_repo, base_branch, head_repo, head_branch):
        matching_prs = run(
            [
                "gh",
                "api",
                "--header",
                "X-GitHub-Api-Version:2022-11-28",
                "--paginate",
                "--method",
                "GET",
                f"/repos/{base_repo.owner}/{base_repo.name}/pulls",
                "-f",
                f"base={base_branch}",
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

        return cls.from_json(base_repo, head_repo, head_branch, json)

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


@cache
def branch_exists(remote: str, branch: str) -> bool:
    """Return True if `remote` has a branch named `branch`."""
    try:
        run(["git", "show-ref", f"refs/remotes/{remote}/{branch}"])
    except CalledProcessError as err:
        if err.returncode == 1:
            return False
        raise

    return True


@cache
def configured_user():
    """Return the configured git user."""
    return User(
        name=run(["git", "config", "--get", "user.name"]),
        email=run(["git", "config", "--get", "user.email"]),
    )


@cache
def current_branch() -> str:
    """Return the name of the current local git branch."""
    return run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"])


@cache
def diff(branches: list[str]) -> str:
    """Return the output of `git diff <branch>...` for the given `branches`."""
    return run(["git", "diff", *branches])


@cache
def log(branches: list[str]) -> list[Commit]:
    """Return the commits from `git log <branch>...` for the given `branches`."""
    return [
        Commit.get(sha)
        for sha in run(
            ["git", "log", "--ignore-missing", *branches, "--format=%H"]
        ).split()
    ]


def push(remote: str, local_branch: str, remote_branch: str) -> None:
    """Force-push <local_branch> to <remote>/<remote_branch>."""
    run(
        ["git", "push", "--force-with-lease", remote, f"{local_branch}:{remote_branch}"]
    )

"""Helpers for working with Git and GitHub."""
from dataclasses import dataclass, field
from subprocess import CalledProcessError
from typing import Optional

from gh_pr_upsert.run import run


@dataclass(frozen=True)
class Commit:
    """A Git commit."""

    sha: str = field(compare=False)
    author_name: str = field(repr=False)
    author_email: str = field(repr=False)
    committer_name: str = field(repr=False)
    committer_email: str = field(repr=False)
    message: str = field(repr=False)
    patch: str = field(repr=False)

    @classmethod
    def make(cls, sha: str):
        """Return the commit with the given SHA."""

        def git_show(format_string: str) -> str:
            """Return the output of `git show` with the given --format string."""
            return run(["git", "show", "--no-patch", f"--format={format_string}", sha])

        return cls(
            sha=sha,
            author_name=git_show("%an"),
            author_email=git_show("%ae"),
            committer_name=git_show("%cn"),
            committer_email=git_show("%ce"),
            message=git_show("%B"),
            patch=run(["git", "show", "--format=", sha]),
        )


@dataclass(frozen=True)
class GitHubRepo:
    """A GitHub repo."""

    owner: str
    name: str
    default_branch: str = field(repr=False, compare=False)
    url: str = field(repr=False, compare=False)
    json: Optional[dict] = field(repr=False, compare=False)

    @classmethod
    def make(cls, url: str):
        """Return the GitHub repo for the given URL."""
        json = run(
            ["gh", "repo", "view", "--json", "owner,name,defaultBranchRef", url],
            json=True,
        )

        return cls(
            owner=json["owner"]["login"],
            name=json["name"],
            default_branch=json["defaultBranchRef"]["name"],
            url=url,
            json=json,
        )

    def create_pull_request(self, base_branch: str, head_branch: str, title: str):
        """Open a new pull request."""

        json = run(
            [
                "gh",
                "api",
                "--method",
                "POST",
                f"/repos/{self.owner}/{self.name}/pulls",
                "-f",
                f"base={base_branch}",
                "-f",
                f"head={head_branch}",
                "-f",
                f"title={title}",
            ],
            json=True,
        )
        return PullRequest.make(repo=self, json=json)

    def pull_requests(self):
        """Return the list of open pull requests on this GitHub repo."""
        json = run(
            ["gh", "api", "--paginate", f"/repos/{self.owner}/{self.name}/pulls"],
            json=True,
        )

        return [
            PullRequest.make(repo=self, json=pull_request_json)
            for pull_request_json in json
        ]

    def pull_request(self, base_branch: str, head_branch: str):
        """Return the open PR for base_branch and head_branch, or None."""
        for pull_request in self.pull_requests():
            if pull_request.base_label != f"{self.owner}:{base_branch}":
                continue

            if pull_request.head_label != f"{self.owner}:{head_branch}":
                continue

            return pull_request

        return None


@dataclass(frozen=True)
class PullRequest:
    """A GitHub pull request."""

    repo: str
    number: int
    html_url: str = field(compare=False, repr=False)
    base_label: str = field(compare=False, repr=False)
    head_label: str = field(compare=False, repr=False)
    json: Optional[dict] = field(compare=False, repr=False)

    @classmethod
    def make(cls, repo: GitHubRepo, json: dict):
        """Create a PullRequest from the given GitHub API JSON data."""
        return PullRequest(
            repo=repo,
            html_url=json["html_url"],
            number=json["number"],
            base_label=json["base"]["label"],
            head_label=json["head"]["label"],
            json=json,
        )

    def close(self) -> None:
        """Close this PullRequest."""
        run(
            [
                "gh",
                "api",
                "--method",
                "PATCH",
                f"/repos/{self.repo.owner}/{self.repo.name}/pulls/{self.number}",
                "-f",
                "state=closed",
            ]
        )


def branch_exists(remote: str, branch: str) -> bool:
    """Return True if `remote` has a branch named `branch`.

    This is based on the local git repo's record of `remote` (from the last
    time it cloned or fetched from `remote`). False positives and negatives
    are possible if this info is out of date.
    """
    try:
        run(["git", "show-ref", f"refs/remotes/{remote}/{branch}"])
    except CalledProcessError as err:
        if err.returncode == 1:
            return False
        raise

    return True


def configured_email() -> str:
    """Return the user's email address from `git config`."""
    return run(["git", "config", "--get", "user.email"])


def configured_username() -> str:
    """Return the user's username from `git config`."""
    return run(["git", "config", "--get", "user.name"])


def current_branch() -> str:
    """Return the name of the current local git branch."""
    return run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"])


def diff(branches: list[str]) -> str:
    """Return the output of `git diff <branch>...` for the given `branches`."""
    return run(["git", "diff", *branches])


def fetch_url(remote: str) -> str:
    """Return the given `remote`'s fetch URL."""
    return run(["git", "remote", "get-url", remote])


def log(branches: list[str], options: Optional[list[str]] = None) -> list[Commit]:
    """Return the commits from `git log <branch>...` for the given `branches`."""
    if options is None:
        options = []

    return [
        Commit.make(sha)
        for sha in run(["git", "log", *options, *branches, "--format=%H"]).split()
    ]


def push(remote: str, branch: str) -> None:
    """Push `branch` to `remote/branch`.

    If `remote/branch` doesn't exist it'll be created.

    If `remote/branch` does exist it'll be updated by force-pushing.

    This will remove any commits from `remote/branch` that don't exist on the
    local `branch`. To see what commits will be removed run:
    `git log remote/branch ^branch`.
    """
    run(["git", "push", "--force-with-lease", remote, f"{branch}:{branch}"])


def there_are_merge_commits(remote: str, base_branch: str, head_branch: str) -> bool:
    """Return True if head_branch or remote_branch has merge commits that aren't on remote/base_branch."""
    branches = [head_branch, f"^{remote}/{base_branch}"]

    if branch_exists(remote, head_branch):
        branches.append(f"{remote}/{head_branch}")

    return bool(log(branches, options=["--merges"]))

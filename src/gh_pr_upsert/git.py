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

    @classmethod
    def get_configured_user(cls):
        return cls(
            name=run(["git", "config", "--get", "user.name"]),
            email=run(["git", "config", "--get", "user.email"]),
        )


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
                "owner,name,nameWithOwner,defaultBranchRef",
                run(["git", "remote", "get-url", remote]),
            ],
            json=True,
        )

        return cls(
            owner=json["owner"]["login"],
            name=json["name"],
            name_with_owner=json["nameWithOwner"],
            default_branch=json["defaultBranchRef"]["name"],
            url=url,
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
    """Return True if `remote` has a branch named `branch`.

    This is based on the local git repo's record of `remote` (from the last
    time it was cloned from or fetched from `remote`). False positives and
    negatives are possible if this local info is out of date.
    """
    try:
        run(["git", "show-ref", f"refs/remotes/{remote}/{branch}"])
    except CalledProcessError as err:
        if err.returncode == 1:
            return False
        raise

    return True


def current_branch() -> str:
    """Return the name of the current local git branch."""
    return run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"])


def diff(branches: list[str]) -> str:
    """Return the output of `git diff <branch>...` for the given `branches`."""
    return run(["git", "diff", *branches])


def log(branches: list[str]) -> list[Commit]:
    """Return the commits from `git log <branch>...` for the given `branches`."""
    return [
        Commit.get(sha) for sha in run(["git", "log", *branches, "--format=%H"]).split()
    ]


def push(base_remote: str, head_remote: str, branch: str) -> None:
    """Force-push <branch> to <head_remote>/<branch>.

    If <head_remote>/<branch> doesn't exist the branch will be created.

    If <head_remote>/<branch> already exists it'll be force-pushed.
    WARNING: This may remove some or all of the commits from
    <head_remote>/<branch>! To see which commits will be removed run:

        log(f"{head_remote}/{branch}", f"^{branch}")

    If <head_remote>/<branch> exists and contains commits that were not
    authored by the configured git user (from `git config`) and are not on
    base_remote's default branch then raise because we don't want to
    potentially remove other user's commits.
    """
    base_repo = GitHubRepo.get(base_remote)
    head_repo = GitHubRepo.get(head_remote)

    if branch_exists(head_remote, branch):
        # The commits that are on the remote branch currently.
        remote_commits = git.log(
            ["f{head_remote}/{branch}", f"^{base_remote}/{base_repo.default_branch}"]
        )

        # The commits that *will* be on the remote branch if we force-push it.
        local_commits = git.log(
            ["f{branch}", f"^{base_remote}/{base_repo.default_branch}"]
        )

        # The commits that will be removed from the remote branch if we force-push it.
        commits_that_would_be_removed = [
            commit for commit in remote_commits if commit not in local_commits
        ]

        for commit in commits_that_would_be_removed:
            if commit.author != User.get_configured_user():
                raise RuntimeError("It's all wrong")

    # If we get here then it's safe to force-push the branch:
    # either the remote branch doesn't exist or it contains only commits
    # authored by the configured git user.
    run(["git", "push", "--force-with-lease", remote, f"{branch}:{branch}"])

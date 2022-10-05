"""Helper functions for working with Git and GitHub."""
from functools import lru_cache
from subprocess import CalledProcessError

from gh_pr_upsert.run import run


def authenticated_username():
    """Return the user's authenticated username from GitHub CLI."""
    return run(["gh", "api", "/user"], json=True)["login"]


def pr_diff():
    """Return the diff of the open PR for the current branch."""
    return run(["gh", "pr", "diff"])


@lru_cache(maxsize=1)
def pr():  # pylint:disable=invalid-name
    """Return a dict of info about the open PR for the current branch.

    Return `None` if there's no open PR for the current branch.
    """
    try:
        response = run(["gh", "pr", "view", "--json", "state,commits"], json=True)
    except CalledProcessError:
        return None

    if response["state"] != "OPEN":
        return None

    return response


@lru_cache(maxsize=1)
def github_repo():
    """Return a dict of info about the GitHub repo."""
    return run(
        ["gh", "repo", "view", "--json", "url,sshUrl,defaultBranchRef"], json=True
    )


def default_branch():
    """Return the name of the GitHub repo's default branch."""
    return github_repo()["defaultBranchRef"]["name"]


def push_urls():
    """Return a list of the GitHub repo's push URLs."""
    return [github_repo()["url"] + ".git", github_repo()["sshUrl"]]


@lru_cache(maxsize=1)
def current_branch():
    """Return the name of the current git branch."""
    return run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"])


def committed_changes():
    """Return the diff of the current local branch to the GitHub default branch."""
    return run(["git", "diff", f"{remote()}/{default_branch()}..."])


def pr_committers():
    """Return the GitHub usernames of all committers to the current branch's PR."""
    committers = set()
    for commit_ in pr()["commits"]:
        for author in commit_["authors"]:
            committers.add(author["login"])
    return committers


def remotes():
    """Return a list of the local git repo's remotes."""
    return run(["git", "remote"]).split()


def push_url(remote_):
    """Return the push URL of the given remote."""
    return run(["git", "remote", "get-url", "--push", remote_])


def remote():
    """
    Return the local git remote name for the GitHub repo, e.g. "origin".

    Return the name of the local git remote that corresponds to the GitHub repo
    that GitHub CLI chooses for this git repo.
    """
    for remote_ in remotes():
        if push_url(remote_) in push_urls():
            return remote_

    raise ValueError("Couldn't find a local git remote that matches the GitHub repo")


def push(force=False):
    """Push the current branch to GitHub."""
    if force:
        run(["git", "push", "--force", remote(), current_branch()])
    else:
        run(["git", "push", remote(), current_branch()])


def create_pr():
    """Open a new PR for the current branch."""
    run(["gh", "pr", "create", "--fill"])

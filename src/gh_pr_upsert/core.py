from gh_pr_upsert import git


class PRUpsertError(Exception):
    """Base class for all exceptions deliberately raised by this module."""


class OnDefaultBranchError(PRUpsertError):
    message = "You must change to a different branch before creating a PR"
    exit_status = 2


class NoChangesError(PRUpsertError):
    message = "Your branch has no changes compared to the default branch"
    exit_status = 3


class OtherPeopleError(PRUpsertError):
    message = "Other people have pushed commits to the PR, not updating it"
    exit_status = 4


@cache
def safe_to_modify_pr(base_remote, base_branch, head_remote, head_branch) -> bool:
    """Return True if no one else has contributed to the PR."""

    if not git.branch_exists(head_remote, head_branch):
        return True

    # The commits that *will* be in the PR if we force-push it.
    local_commits = git.log(["f{head_branch}", f"^{base_remote}/{base_branch}"])

    # The commits that are in the PR currently.
    remote_commits = git.log(
        ["f{head_remote}/{head_branch}", f"^{base_remote}/{base_branch}"]
    )

    if local_commits == remote_commits:
        return True

    # The commits that will be removed from the PR if we force-push it.
    commits_that_would_be_removed = [
        commit for commit in remote_commits if commit not in local_commits
    ]

    for commit in commits_that_would_be_removed:
        if not (
            commit.author_name == git.configured_username()
            and commit.author_email == git.configured_email()
        ):
            return False

    return True


def pr_upsert(base_remote, base_branch, head_remote, title, body):
    base_repo = git.GitHubRepo.make(git.fetch_url(base_remote))
    head_repo = git.GitHubRepo.make(git.fetch_url(head_remote))

    if base_repo == head_repo and git.current_branch() == base_branch:
        raise SameBranchError()

    if not git.diff([git.current_branch(), f"^{base_remote}/{base_branch}"]):
        existing_pr = git.existing_pr(base_remote, base_branch, head_branch)
        if existing_pr and safe_to_modify_pr():
            existing_pr.close()

        raise NoChangesError()

    if safe_to_modify_pr():
        git.push(base_remote, git.current_branch(), base_branch)

    pr = base_repo.get_pull_request(base_branch, head_repo, head_branch)

    if not pr:
        pr = github.create_pull_request(
            base_branch, head_repo, head_branch, title, body
        )

    print(pr.html_url)

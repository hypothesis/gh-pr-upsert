from gh_pr_upsert import git
from gh_pr_upsert.exceptions import NoChangesError, OtherPeopleError, SameBranchError


def pr_upsert(
    base_repo,
    base_branch,
    local_branch,
    head_repo,
    head_branch,
    title,
    body,
    close_comment,
):  # pylint:disable=too-many-arguments
    # You can't send a PR to merge a branch into itself.
    if base_repo == head_repo and base_branch == head_branch:
        raise SameBranchError()

    # The list of users who have commits on the remote branch.
    commits = git.log(
        (
            f"{head_repo.remote}/{head_branch}",
            f"^{local_branch}",
            f"^{base_repo.remote}/{base_branch}",
        )
    )

    other_authors = {
        commit.author for commit in commits if commit.author != git.configured_user()
    }

    other_committers = {
        commit.committer
        for commit in commits
        if commit.committer != git.configured_user()
    }

    other_contributors = other_authors | other_committers

    # The changes that we have locally.
    local_diff = git.diff((local_branch, f"^{base_repo.remote}/{base_branch}"))

    # The existing PR or None.
    pull_request = git.PullRequest.get(base_repo, base_branch, head_repo, head_branch)

    # If there are no local changes then close any existing PR.
    if not local_diff:
        if pull_request and not other_contributors:
            print(f"Closed PR {pull_request.html_url}")
            pull_request.close(close_comment)

        raise NoChangesError()

    # The changes that already exist on the remote branch.
    if git.branch_exists(head_repo.remote, head_branch):
        remote_diff = git.diff(
            (f"{head_repo.remote}/{head_branch}", f"^{base_repo.remote}/{base_branch}")
        )
    else:
        remote_diff = None

    # Force-push any local changes to the remote branch.
    if local_diff != remote_diff:
        if other_contributors:
            raise OtherPeopleError()

        git.push(head_repo.remote, local_branch, head_branch)

    # Create a PR if there isn't one already.
    if not pull_request:
        pull_request = git.PullRequest.create(
            base_repo, base_branch, head_repo, head_branch, title, body
        )

    print(pull_request.html_url)

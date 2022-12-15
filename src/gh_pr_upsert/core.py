from gh_pr_upsert import git
from gh_pr_upsert.exceptions import NoChangesError, OtherPeopleError, SameBranchError


def pr_upsert(base_remote, head_remote, title, body, close_comment):
    base_repo = git.GitHubRepo.get(base_remote)
    base_branch = base_repo.default_branch
    head_repo = git.GitHubRepo.get(head_remote)
    head_branch = git.current_branch()

    # You can't send a PR to merge a branch into itself.
    if base_repo == head_repo and base_branch == head_branch:
        raise SameBranchError()

    # The list of users who have commits on the remote branch.
    other_contributors = {
        commit.author
        for commit in git.log(
            (
                f"{head_remote}/{head_branch}",
                f"^{head_branch}",
                f"^{base_remote}/{base_branch}",
            )
        )
        if commit.author != git.configured_user()
    }

    # It's safe to modify the remote branch if no other users have commits on it.
    safe_to_modify = other_contributors == set()

    # The changes that we have locally.
    local_diff = git.diff([head_branch, f"^{base_remote}/{base_branch}"])

    # The existing PR or None.
    pull_request = git.PullRequest.get(base_repo, head_repo, head_branch)

    # If there are no local changes then close any existing PR.
    if not local_diff:
        if pull_request and safe_to_modify:
            print(f"Closed PR {pull_request.html_url}")
            pull_request.close(close_comment)

        raise NoChangesError()

    # The changes that already exist on the remote branch.
    if git.branch_exists(head_remote, head_branch):
        remote_diff = git.diff(
            [f"{head_remote}/{head_branch}", f"^{base_remote}/{base_branch}"]
        )
    else:
        remote_diff = None

    # Force-push any local changes to the remote branch.
    if local_diff != remote_diff:
        if not safe_to_modify:
            raise OtherPeopleError()

        git.push(head_remote, head_branch)

    # Create a PR if there isn't one already.
    if not pull_request:
        pull_request = git.PullRequest.create(
            base_repo, head_repo, head_branch, title, body
        )

    print(pull_request.html_url)

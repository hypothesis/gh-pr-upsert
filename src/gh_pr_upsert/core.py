from gh_pr_upsert import git
from gh_pr_upsert.exceptions import SameBranchError


def pr_upsert(base_remote, base_branch, head_remote, title, body, close_comment):
    # The repo where we'll open the PR.
    base_repo = git.GitHubRepo.get(base_remote)

    # The branch that the PR will request to be merged into.
    base_branch = base_repo.default_branch

    # The repo that we'll push the branch containing our commits to.
    head_repo = git.GitHubRepo.get(head_remote)

    # The branch that contains the commits we want to push.
    head_branch = git.current_branch()

    # You can't send a PR to merge one branch into itself.
    if base_repo == head_repo and base_branch == head_branch:
        raise SameBranchError()

    # The list of users who have commits on the remote branch.
    contributors = set(
        [
            commit.author
            for commit in git.log(
                f"{head_remote}/{head_branch}",
                f"^{head_branch}",
                f"^{base_remote}/{base_branch}",
            )
        ]
    )

    # It's safe to modify the remote branch if only the current user has commits on it.
    safe_to_modify = contributors == {git.configured_user()}

    # The changes that we have locally.
    local_diff = git.diff([head_branch, f"^{base_remote}/{base_branch}"])

    # The existing PR or None.
    pr = PullRequest.get(base_repo, head_repo, head_branch)

    # If there are no local changes then close any existing PR.
    if not local_diff:
        if pr and safe_to_modify:
            pr.close(close_comment)

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
    if not pr:
        pr = github.PullRequest.create()

    print(pr.url)

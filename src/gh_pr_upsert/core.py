from gh_pr_upsert import git


class PRUpsertError(Exception):
    """Base class for all exceptions deliberately raised by this module."""

    message = None
    exit_status = None


class OnDefaultBranchError(PRUpsertError):
    message = "You must change to a branch before creating a PR"
    exit_status = 2


class NoChangesError(PRUpsertError):
    message = "Your branch has no changes compared to the default branch"
    exit_status = 3


class OtherPeopleError(PRUpsertError):
    message = "Other people have pushed commits to the PR, not updating it"
    exit_status = 4


class ExistingPRError(PRUpsertError):
    message = "Your local changes are the same as the open PR, there's nothing to do"
    exit_status = 5


def pr_upsert():
    if git.current_branch() == git.default_branch():
        raise OnDefaultBranchError()

    if not git.committed_changes():
        raise NoChangesError()

    if not git.pr():
        print("There's no PR for this branch yet, creating one")
        git.push()
        git.create_pr()
    else:
        print("There's already an open PR for this branch")

        if git.committed_changes() == git.pr_diff():
            raise ExistingPRError()

        print("Your local changes are different from the open PR")

        if git.pr_committers() != {git.authenticated_username()}:
            raise OtherPeopleError()

        print("No one else has pushed to the PR, updating it")
        git.push(force=True)

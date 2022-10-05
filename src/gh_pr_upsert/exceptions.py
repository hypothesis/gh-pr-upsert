class PRUpsertError(Exception):
    """Base class for all exceptions deliberately raised by gh_pr_upsert."""

    message = ""
    exit_status = 1


class SameBranchError(PRUpsertError):
    message = "You must change to a different branch before creating a PR"
    exit_status = 2


class NoChangesError(PRUpsertError):
    message = "Your branch has no changes compared to the default branch"
    exit_status = 3


class OtherPeopleError(PRUpsertError):
    message = "Other people have pushed commits to the branch, not updating it"
    exit_status = 4

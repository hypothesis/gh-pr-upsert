from gh_pr_upsert import git


class PRUpsertError(Exception):
    """Base class for all exceptions deliberately raised by this module."""


class OnDefaultBranchError(PRUpsertError):
    message = "You must change to a branch before creating a PR"
    exit_status = 2


class NoChangesError(PRUpsertError):
    message = "Your branch has no changes compared to the default branch"
    exit_status = 3


class OtherPeopleError(PRUpsertError):
    message = "Other people have pushed commits to the PR, not updating it"
    exit_status = 4


def push(remote, head_branch, base_branch):
    if git.branch_exists(remote, head_branch):
        local_commits = git.log([f"^{remote}/{base_branch}", head_branch])
        remote_commits = git.log(
            [f"^{remote}/{base_branch}", f"{remote}/{head_branch}"]
        )

        if local_commits == remote_commits:
            return

        commits_to_delete = [
            commit for commit in remote_commits if commit not in local_commits
        ]

        for commit in commits_to_delete:
            if not (
                commit.author_name == git.configured_username()
                and commit.author_email == git.configured_email()
            ):
                raise OtherPeopleError()

    git.push(remote, head_branch)


def pr_upsert(remote, base_branch, head_branch, title):
    github = git.GitHubRepo.make(git.fetch_url(remote))

    if head_branch == github.default_branch:
        raise OnDefaultBranchError()

    if git.there_are_merge_commits(remote, base_branch, head_branch):
        raise NotImplementedError("gh-pr-upsert doesn't work when merge commits are present")

    if not git.diff([head_branch, f"^{remote}/{base_branch}"]):
        if pull_request := existing_pr(remote, base_branch, head_branch):
            pull_request.close()
        raise NoChangesError()

    push(remote, head_branch, base_branch)

    pr = github.pull_request(base_branch, head_branch)

    if not pr:
        pr = github.create_pull_request(base_branch, head_branch, title)

    print(pr.html_url)

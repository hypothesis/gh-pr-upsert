from unittest.mock import call, sentinel

import pytest

from gh_pr_upsert import core
from gh_pr_upsert.exceptions import NoChangesError, OtherPeopleError, SameBranchError


class TestPRUpsert:
    def test_it(self, base_repo, capsys, git, head_repo):
        core.pr_upsert(
            sentinel.base_remote,
            sentinel.head_remote,
            sentinel.title,
            sentinel.body,
            sentinel.close_comment,
        )

        # It gets the base and head GitHub repos.
        assert git.GitHubRepo.get.call_args_list == [
            call(sentinel.base_remote),
            call(sentinel.head_remote),
        ]

        # It gets the current branch.
        git.current_branch.assert_called_once_with()

        current_branch = git.current_branch.return_value
        default_branch = base_repo.default_branch

        # It gets the list of commits on the remote branch compared to the local branch.
        git.log.assert_called_once_with(
            (
                f"{sentinel.head_remote}/{current_branch}",
                f"^{current_branch}",
                f"^{sentinel.base_remote}/{default_branch}",
            )
        )

        assert git.diff.call_args_list == [
            # It gets the diff of the local branch.
            call(
                [
                    current_branch,
                    f"^{sentinel.base_remote}/{default_branch}",
                ]
            ),
            # It gets the diff of the remote branch.
            call(
                [
                    f"{sentinel.head_remote}/{current_branch}",
                    f"^{sentinel.base_remote}/{default_branch}",
                ]
            ),
        ]

        # It gets the existing PR.
        git.PullRequest.get.assert_called_once_with(
            base_repo, head_repo, current_branch
        )

        # It checks whether the remote branch exists.
        git.branch_exists.assert_called_once_with(sentinel.head_remote, current_branch)

        # It does not call `git push` because the local and remote diffs are the same.
        git.push.assert_not_called()

        # It does not create a PR because one already exists.
        git.PullRequest.create.assert_not_called()

        # It doesn't close the PR because there was a diff.
        git.PullRequest.get.return_value.close.assert_not_called()

        # It prints out the PR's URL.
        assert capsys.readouterr().out.strip() == str(
            git.PullRequest.get.return_value.html_url
        )

    def test_it_raises_if_the_base_and_head_branch_are_the_same(self, base_repo, git):
        git.GitHubRepo.get.side_effect = [base_repo, base_repo]
        git.current_branch.return_value = base_repo.default_branch

        with pytest.raises(SameBranchError):
            core.pr_upsert(
                sentinel.remote,
                sentinel.remote,
                sentinel.title,
                sentinel.body,
                sentinel.close_comment,
            )

    def test_if_there_are_no_changes_it_closes_any_existing_pr(self, git):
        git.diff.return_value = ""

        with pytest.raises(NoChangesError):
            core.pr_upsert(
                sentinel.base_remote,
                sentinel.head_remote,
                sentinel.title,
                sentinel.body,
                sentinel.close_comment,
            )

        git.PullRequest.get.return_value.close.assert_called_once_with(
            sentinel.close_comment
        )

    def test_it_doesnt_close_prs_that_have_other_contributors(
        self, commit_factory, git
    ):
        git.diff.return_value = ""
        git.log.return_value.append(commit_factory())

        with pytest.raises(NoChangesError):
            core.pr_upsert(
                sentinel.base_remote,
                sentinel.head_remote,
                sentinel.title,
                sentinel.body,
                sentinel.close_comment,
            )

        git.PullRequest.get.return_value.close.assert_not_called()

    def test_if_the_remote_branch_doesnt_exist_it_creates_it(self, git):
        git.branch_exists.return_value = False

        core.pr_upsert(
            sentinel.base_remote,
            sentinel.head_remote,
            sentinel.title,
            sentinel.body,
            sentinel.close_comment,
        )

        git.push.assert_called_once_with(
            sentinel.head_remote, git.current_branch.return_value
        )

    def test_if_the_remote_branch_already_exists_it_updates_it(self, git):
        git.diff.side_effect = [sentinel.local_diff, sentinel.remote_diff]

        core.pr_upsert(
            sentinel.base_remote,
            sentinel.head_remote,
            sentinel.title,
            sentinel.body,
            sentinel.close_comment,
        )

        git.push.assert_called_once_with(
            sentinel.head_remote, git.current_branch.return_value
        )

    def test_it_doesnt_push_the_remote_branch_if_there_are_other_contributors(
        self, commit_factory, git
    ):
        git.diff.side_effect = [sentinel.local_diff, sentinel.remote_diff]
        git.log.return_value.append(commit_factory())

        with pytest.raises(OtherPeopleError):
            core.pr_upsert(
                sentinel.base_remote,
                sentinel.head_remote,
                sentinel.title,
                sentinel.body,
                sentinel.close_comment,
            )

        git.push.assert_not_called()

    def test_if_the_pr_doesnt_exist_it_creates_one(self, base_repo, git, head_repo):
        git.PullRequest.get.return_value = None

        core.pr_upsert(
            sentinel.base_remote,
            sentinel.head_remote,
            sentinel.title,
            sentinel.body,
            sentinel.close_comment,
        )

        git.PullRequest.create.assert_called_once_with(
            base_repo,
            head_repo,
            git.current_branch.return_value,
            sentinel.title,
            sentinel.body,
        )

    @pytest.fixture(autouse=True)
    def git(self, mocker, base_repo, head_repo, user, commit_factory):
        git = mocker.patch("gh_pr_upsert.core.git", autospec=True)

        git.GitHubRepo.get.side_effect = [base_repo, head_repo]

        # Make `git log` return two commits both by the configured user.
        git.configured_user.return_value = user
        git.log.return_value = commit_factory.create_batch(
            2, author=git.configured_user.return_value
        )

        return git

from unittest.mock import sentinel

import pytest

from gh_pr_upsert.core import (
    ExistingPRError,
    NoChangesError,
    OnDefaultBranchError,
    OtherPeopleError,
    pr_upsert,
)


class TestPRUpsert:
    def test_if_there_isnt_already_a_PR_it_creates_one(self, git, capsys):
        git.pr.return_value = None

        pr_upsert()

        assert (
            capsys.readouterr().out.strip()
            == "There's no PR for this branch yet, creating one"
        )
        git.push.assert_called_once_with()
        git.create_pr.assert_called_once_with()

    def test_if_theres_an_existing_PR_it_updates_it(self, git, capsys):
        # Make it so that the open PR contains only commits by the
        # authenticated user. Otherwise pr_upsert() will refuse to force-push
        # the PR.
        git.pr_committers.return_value = {git.authenticated_username.return_value}

        pr_upsert()

        git.push.assert_called_once_with(force=True)
        git.create_pr.assert_not_called()
        assert capsys.readouterr().out.strip().split("\n") == [
            "There's already an open PR for this branch",
            "Your local changes are different from the open PR",
            "No one else has pushed to the PR, updating it",
        ]

    def test_it_raises_if_youre_on_the_default_branch(self, git):
        git.current_branch.return_value = git.default_branch.return_value

        with pytest.raises(OnDefaultBranchError):
            pr_upsert()

    def test_it_raises_if_there_are_no_committed_changes(self, git):
        git.committed_changes.return_value = ""

        with pytest.raises(NoChangesError):
            pr_upsert()

    def test_it_raises_if_theres_an_equivalent_pr_open(self, git):
        git.committed_changes.return_value = git.pr_diff.return_value

        with pytest.raises(ExistingPRError):
            pr_upsert()

    def test_it_raises_if_theres_a_pr_with_other_peoples_commits(self, git):
        git.pr_committers.return_value = {sentinel.committer_1, sentinel.committer_2}
        git.authenticated_username.return_value = sentinel.committer_1

        with pytest.raises(OtherPeopleError):
            pr_upsert()


@pytest.fixture(autouse=True)
def git(mocker):
    return mocker.patch("gh_pr_upsert.core.git", autospec=True)

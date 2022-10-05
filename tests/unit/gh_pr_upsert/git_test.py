from subprocess import CalledProcessError
from unittest.mock import sentinel

import pytest

from gh_pr_upsert import git


class TestAuthenticatedUsername:
    def test_it(self, run):
        run.return_value = {"login": sentinel.username}

        username = git.authenticated_username()

        run.assert_called_once_with(["gh", "api", "/user"], json=True)
        assert username == sentinel.username


class TestPRDiff:
    def test_it(self, run):
        diff = git.pr_diff()

        run.assert_called_once_with(["gh", "pr", "diff"])
        assert diff == run.return_value


class TestPR:
    def test_it_returns_the_open_pr(self, run):
        run.return_value = {"state": "OPEN"}

        pr = git.pr()

        run.assert_called_once_with(
            ["gh", "pr", "view", "--json", "state,commits"], json=True
        )
        assert pr == run.return_value

    def test_it_returns_None_if_theres_no_open_pr(self, run):
        run.return_value = {"state": "CLOSED"}

        assert git.pr() is None

    def test_it_returns_None_if_the_command_fails(self, run):
        run.side_effect = CalledProcessError(
            returncode=sentinel.returncode, cmd=sentinel.cmd
        )

        assert git.pr() is None

    @pytest.fixture(autouse=True)
    def cache_clear(self):
        git.pr.cache_clear()


class TestGitHubRepo:
    def test_it(self, run):
        repo = git.github_repo()

        run.assert_called_once_with(
            ["gh", "repo", "view", "--json", "url,sshUrl,defaultBranchRef"], json=True
        )
        assert repo == run.return_value

    @pytest.fixture(autouse=True)
    def cache_clear(self):
        git.github_repo.cache_clear()


class TestDefaultBranch:
    def test_it(self, run):
        run.return_value = {"defaultBranchRef": {"name": sentinel.default_branch_name}}

        branch_name = git.default_branch()

        run.assert_called_once_with(
            ["gh", "repo", "view", "--json", "url,sshUrl,defaultBranchRef"], json=True
        )
        assert branch_name == sentinel.default_branch_name

    @pytest.fixture(autouse=True)
    def cache_clear(self):
        git.github_repo.cache_clear()


class TestPushURLs:
    def test_it(self, run):
        run.return_value = {"url": "test_url", "sshUrl": "test_ssh_url"}

        urls = git.push_urls()

        run.assert_called_once_with(
            ["gh", "repo", "view", "--json", "url,sshUrl,defaultBranchRef"], json=True
        )
        assert urls == ["test_url.git", "test_ssh_url"]

    @pytest.fixture(autouse=True)
    def cache_clear(self):
        git.github_repo.cache_clear()


class TestCurrentBranch:
    def test_it(self, run):
        current_branch = git.current_branch()

        run.assert_called_once_with(
            ["git", "symbolic-ref", "--quiet", "--short", "HEAD"]
        )
        assert current_branch == run.return_value

    @pytest.fixture(autouse=True)
    def cache_clear(self):
        git.current_branch.cache_clear()


class TestCommittedChanges:
    def test_it(self, run):
        diff = git.committed_changes()

        run.assert_called_once_with(["git", "diff", "origin/main..."])
        assert diff == run.return_value

    @pytest.fixture(autouse=True)
    def remote(self, mocker):
        return mocker.patch(
            "gh_pr_upsert.git.remote", autospec=True, return_value="origin"
        )

    @pytest.fixture(autouse=True)
    def default_branch(self, mocker):
        return mocker.patch(
            "gh_pr_upsert.git.default_branch", autospec=True, return_value="main"
        )


class TestPRCommitters:
    def test_it(self, run):
        run.return_value = {
            "state": "OPEN",
            "commits": [
                {"authors": [{"login": "author_1"}]},
                # Commits can have multiple authors.
                {"authors": [{"login": "author_2"}, {"login": "author_3"}]},
                # Duplicates should be removed.
                {"authors": [{"login": "author_1"}]},
            ],
        }

        committers = git.pr_committers()

        run.assert_called_once_with(
            ["gh", "pr", "view", "--json", "state,commits"], json=True
        )
        assert committers == {"author_1", "author_2", "author_3"}

    @pytest.fixture(autouse=True)
    def cache_clear(self):
        git.pr.cache_clear()


class TestRemotes:
    def test_it(self, run):
        run.return_value = "origin\nupstream"

        remotes = git.remotes()

        run.assert_called_once_with(["git", "remote"])
        assert remotes == ["origin", "upstream"]


class TestPushURL:
    def test_it(self, run):
        url = git.push_url(sentinel.remote)

        run.assert_called_once_with(
            ["git", "remote", "get-url", "--push", sentinel.remote]
        )
        assert url == run.return_value


class TestRemote:
    def test_it(self):
        assert git.remote() == "remote_1"

    def test_it_raises_ValueError_if_no_remotes_match(self, remotes):
        remotes.return_value = ["non_matching_remote_1", "non_matching_remote_2"]

        with pytest.raises(ValueError):
            git.remote()

    @pytest.fixture(autouse=True)
    def remotes(self, mocker):
        return mocker.patch(
            "gh_pr_upsert.git.remotes",
            autospec=True,
            return_value=["remote_1", "remote_2"],
        )

    @pytest.fixture(autouse=True)
    def push_url(self, mocker):
        return mocker.patch(
            "gh_pr_upsert.git.push_url",
            autospec=True,
            side_effect=lambda remote: f"push_url for: {remote}",
        )

    @pytest.fixture(autouse=True)
    def push_urls(self, mocker):
        return mocker.patch(
            "gh_pr_upsert.git.push_urls",
            autospec=True,
            return_value=["some_other_push_url", "push_url for: remote_1"],
        )


class TestPush:
    @pytest.mark.parametrize(
        "force,expected_command",
        [
            (
                True,
                ["git", "push", "--force", sentinel.remote, sentinel.current_branch],
            ),
            (False, ["git", "push", sentinel.remote, sentinel.current_branch]),
        ],
    )
    def test_it(self, force, expected_command, run):
        git.push(force=force)

        run.assert_called_once_with(expected_command)

    @pytest.fixture(autouse=True)
    def remote(self, mocker):
        return mocker.patch(
            "gh_pr_upsert.git.remote", autospec=True, return_value=sentinel.remote
        )

    @pytest.fixture(autouse=True)
    def current_branch(self, mocker):
        return mocker.patch(
            "gh_pr_upsert.git.current_branch",
            autospec=True,
            return_value=sentinel.current_branch,
        )


class TestCreatePR:
    def test_it(self, run):
        git.create_pr()

        run.assert_called_once_with(["gh", "pr", "create", "--fill"])


@pytest.fixture(autouse=True)
def run(mocker):
    return mocker.patch("gh_pr_upsert.git.run", autospec=True)

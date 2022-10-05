from importlib.metadata import version
from subprocess import CalledProcessError
from unittest.mock import call, sentinel

import pytest

from gh_pr_upsert.cli import cli
from gh_pr_upsert.exceptions import NoChangesError


def test_help():
    with pytest.raises(SystemExit) as exc_info:
        cli(["--help"])

    assert not exc_info.value.code


def test_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli(["--version"])

    assert capsys.readouterr().out.strip() == version("gh-pr-upsert")
    assert not exc_info.value.code


def test_defaults(core, base_repo, head_repo, git):
    cli([])

    assert git.GitHubRepo.get.call_args_list == [call("origin"), call("origin")]
    git.current_branch.assert_called_once_with()
    core.pr_upsert.assert_called_once_with(
        base_repo,
        base_repo.default_branch,
        git.current_branch.return_value,
        head_repo,
        git.current_branch.return_value,
        "Automated changes by gh-pr-upsert",
        "Automated changes by [gh-pr-upsert](https://github.com/hypothesis/gh-pr-upsert).",
        "It looks like this PR isn't needed anymore, closing it.",
    )


def test_options(core, base_repo, head_repo, git):
    cli(
        [
            "--base-remote",
            "my_base_remote",
            "--base-branch",
            "my_base_branch",
            "--local-branch",
            "my_local_branch",
            "--head-remote",
            "my_head_remote",
            "--head-branch",
            "my_head_branch",
            "--title",
            "my_title",
            "--body",
            "my_body",
            "--close-comment",
            "my_close_comment",
        ]
    )

    assert git.GitHubRepo.get.call_args_list == [
        call("my_base_remote"),
        call("my_head_remote"),
    ]
    core.pr_upsert.assert_called_once_with(
        base_repo,
        "my_base_branch",
        "my_local_branch",
        head_repo,
        "my_head_branch",
        "my_title",
        "my_body",
        "my_close_comment",
    )


def test_PRUpsertError(capsys, core):
    core.pr_upsert.side_effect = NoChangesError()

    with pytest.raises(SystemExit) as exc_info:
        cli([])

    assert capsys.readouterr().out.strip() == NoChangesError.message
    assert exc_info.value.code == NoChangesError.exit_status


def test_CalledProcessError(core):
    error = core.pr_upsert.side_effect = CalledProcessError(23, sentinel.cmd)

    with pytest.raises(CalledProcessError) as exc_info:
        cli([])

    assert exc_info.value == error


def test_it_prints_stdout_and_stderr_from_CalledProcessErrors(capsys, core):
    core.pr_upsert.side_effect = CalledProcessError(
        23, sentinel.cmd, b"output", b"errors"
    )

    with pytest.raises(CalledProcessError):
        cli([])

    assert capsys.readouterr().out.strip() == "errors\noutput"


@pytest.fixture(autouse=True)
def core(mocker):
    return mocker.patch("gh_pr_upsert.cli.core", autospec=True)


@pytest.fixture(autouse=True)
def git(mocker, base_repo, head_repo):
    git = mocker.patch("gh_pr_upsert.cli.git", autospec=True)
    git.GitHubRepo.get.side_effect = [base_repo, head_repo]
    return git

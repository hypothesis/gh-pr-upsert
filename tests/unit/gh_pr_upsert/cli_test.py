from importlib.metadata import version
from subprocess import CalledProcessError
from unittest.mock import sentinel

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


def test_defaults(core):
    cli([])

    core.pr_upsert.assert_called_once_with(
        "origin",
        "origin",
        "Automated changes by gh-pr-upsert",
        "Automated changes by [gh-pr-upsert](https://github.com/hypothesis/gh-pr-upsert).",
        "It looks like this PR isn't needed anymore, closing it.",
    )


def test_options(core):
    cli(
        [
            "--base",
            "my_base_remote",
            "--head",
            "my_head_remote",
            "--title",
            "my_title",
            "--body",
            "my_body",
            "--close-comment",
            "my_close_comment",
        ]
    )

    core.pr_upsert.assert_called_once_with(
        "my_base_remote", "my_head_remote", "my_title", "my_body", "my_close_comment"
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

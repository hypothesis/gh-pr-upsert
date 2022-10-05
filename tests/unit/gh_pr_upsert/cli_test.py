from importlib.metadata import version
from subprocess import CalledProcessError

import pytest

from gh_pr_upsert.cli import PRUpsertError, cli


def test_cli(core):
    """Test the happy path.

    Test when gh-pr-upsert is run with no command line arguments and
    pr_upsert() exits successfully.
    """
    cli([])

    core.pr_upsert.assert_called_once_with()


def test_cli_help(core):
    """Test gh-pr-upsert --help."""
    with pytest.raises(SystemExit) as exc_info:
        cli(["--help"])

    assert not exc_info.value.code
    core.pr_upsert.assert_not_called()


def test_cli_version(core, capsys):
    """Test gh-pr-upsert --version."""
    with pytest.raises(SystemExit) as exc_info:
        cli(["--version"])

    assert not exc_info.value.code
    assert capsys.readouterr().out.strip() == version("gh-pr-upsert")
    core.pr_upsert.assert_not_called()


def test_cli_expected_exception(core, capsys):
    core.pr_upsert.side_effect = PRUpsertError()
    core.pr_upsert.side_effect.message = "test_error_message"
    core.pr_upsert.side_effect.exit_status = 42

    with pytest.raises(SystemExit) as exc_info:
        cli([])

    core.pr_upsert.assert_called_once_with()
    assert exc_info.value.code == 42
    assert capsys.readouterr().out.strip() == "test_error_message"


def test_cli_unexpected_exception(core, capsys):
    core.pr_upsert.side_effect = CalledProcessError(42, "test_command")
    core.pr_upsert.side_effect.stdout = b"output"
    core.pr_upsert.side_effect.stderr = b"error_output"

    with pytest.raises(CalledProcessError) as exc_info:
        cli([])

    core.pr_upsert.assert_called_once_with()
    assert exc_info.value.returncode == 42
    assert capsys.readouterr().out.strip() == "error_output\noutput"


# If subprocess.run() is called without capture_output=True when
# CalledProcessError.stderr and stdout are None.
def test_cli_unexpected_exception_with_no_capture_output(core, capsys):
    core.pr_upsert.side_effect = CalledProcessError(42, "test_command")

    with pytest.raises(CalledProcessError) as exc_info:
        cli([])

    core.pr_upsert.assert_called_once_with()
    assert exc_info.value.returncode == 42
    assert not capsys.readouterr().out


@pytest.fixture(autouse=True)
def core(mocker):
    return mocker.patch("gh_pr_upsert.cli.core", autospec=True)

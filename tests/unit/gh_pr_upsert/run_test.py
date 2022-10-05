import json
from subprocess import CompletedProcess

import pytest

from gh_pr_upsert.run import run


def test_run(subprocess):
    subprocess.run.return_value = CompletedProcess(
        "args", returncode=42, stdout=b"test_output\n"
    )

    result = run("test_command")

    subprocess.run.assert_called_once_with(
        "test_command", check=True, capture_output=True
    )
    assert result == "test_output"


def test_run_prints_commands_in_debug_mode(capsys, os):
    os.environ["DEBUG"] = "yes"

    run("test_command")

    assert capsys.readouterr().out.strip() == "test_command"


def test_run_loads_json(subprocess):
    expected_result = {"foo": "bar"}
    subprocess.run.return_value = CompletedProcess(
        "args", returncode=42, stdout=json.dumps(expected_result)
    )

    assert run("test_command", json=True) == expected_result


@pytest.fixture(autouse=True)
def os(mocker):
    os = mocker.patch("gh_pr_upsert.run.os", autospec=True)
    os.environ = {}
    return os


@pytest.fixture(autouse=True)
def subprocess(mocker):
    return mocker.patch("gh_pr_upsert.run.subprocess", autospec=True)

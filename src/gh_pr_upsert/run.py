"""Helper functions for running subprocesses."""

import json as json_
import os
import subprocess


def run(cmd, json=False):
    """Run a command in a subprocess and returns its stdout."""
    if os.environ.get("DEBUG") == "yes":
        print(cmd)

    stdout = subprocess.run(cmd, check=True, capture_output=True).stdout

    if json:
        return json_.loads(stdout)

    return stdout.decode("utf-8").strip()

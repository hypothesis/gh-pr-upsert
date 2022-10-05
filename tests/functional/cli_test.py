from subprocess import run


def test_help():
    """Test the gh-pr-upsert --help command."""
    run(["gh-pr-upsert", "--help"], check=True)


def test_version():
    """Test the gh-pr-upsert --version command."""
    run(["gh-pr-upsert", "--version"], check=True)

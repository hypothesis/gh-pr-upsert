import factory.random
import pytest
from pytest_factoryboy import register

from tests import factories

register(factories.UserFactory)
register(factories.CommitFactory)
register(factories.GitHubRepoFactory)
register(factories.GitHubRepoFactory, _name="base_repo")
register(factories.GitHubRepoFactory, _name="head_repo")
register(factories.PullRequestFactory)


@pytest.fixture(scope="session", autouse=True)
def factory_boy_random_seed():
    # Set factory_boy's random seed so that it produces the same random values
    # in each run of the tests.
    # See: https://factoryboy.readthedocs.io/en/latest/index.html#reproducible-random-values
    factory.random.reseed_random("hypothesis/gh-pr-upsert")

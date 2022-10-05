import factory

from gh_pr_upsert import git


class UserFactory(factory.Factory):
    class Meta:
        model = git.User

    name = factory.Sequence(lambda n: f"User {n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")


class CommitFactory(factory.Factory):
    class Meta:
        model = git.Commit

    sha = factory.Faker("sha1")
    author = factory.SubFactory(UserFactory)


class GitHubRepoFactory(factory.Factory):
    class Meta:
        model = git.GitHubRepo

    remote = "origin"
    owner = factory.Sequence(lambda n: f"user-{n}")
    name = factory.Sequence(lambda n: f"repo-{n}")
    name_with_owner = factory.LazyAttribute(lambda o: f"{o.owner}/{o.name}")
    default_branch = factory.Faker("random_element", elements=["main", "master"])
    url = factory.LazyAttribute(lambda o: f"https://github.com/{o.owner}/{o.name}")
    json = None


class PullRequestFactory(factory.Factory):
    class Meta:
        model = git.PullRequest

    base_repo = factory.SubFactory(GitHubRepoFactory)
    head_repo = factory.SubFactory(GitHubRepoFactory)
    head_branch = factory.Faker("word")
    number = factory.Sequence(lambda n: n)
    html_url = factory.LazyAttribute(
        lambda o: f"https://github.com/{o.base_repo.owner}/{o.base_repo.name}/pull/{o.number}"
    )
    json = None

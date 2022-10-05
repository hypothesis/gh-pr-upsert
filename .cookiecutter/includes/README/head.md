The `gh pr-upsert` command will create a new pull request (PR) with the commits
on your current branch, generating a PR title and body from your commit
messages:

```terminal
$ gh pr-upsert
There's no PR for this branch yet, creating one
```

Unlike `gh pr create`, `gh pr-upsert` always pushes your branch directly to the
GitHub repo before opening a PR. It's a non-interactive command and doesn't ask
you whether or not to push or offer to create a fork.

Also unlike `gh pr create`, if there's already a PR for the branch then `gh
pr-upsert` will force push it:

```terminal
$ gh pr-upsert
There's already an open PR for this branch
Your local changes are different from the open PR
No one else has pushed to the PR, updating it
```

Requires [Git](https://git-scm.com/) and [GitHub CLI](https://cli.github.com/)
to be installed.

To install the latest version of `gh-pr-upsert` as a GitHub CLI extension run:

```terminal
gh extension install hypothesis/gh-pr-upsert
```

Then to upgrade to a new version run `gh extension upgrade gh-pr-upsert`.
To remove the extension run `gh extension remove gh-pr-upsert`.

Alternatively you can install `gh-pr-upsert` as a Python package and the
command will be `gh-pr-upsert` rather than `gh pr-upsert`. See below for
details.

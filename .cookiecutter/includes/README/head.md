`gh-pr-upsert` creates or updates a GitHub pull request (PR) with the commits
on your current branch:

```console
$ git clone https://github.com/$YOUR_OWNER/$YOUR_REPO.git
$ cd $YOUR_REPO
$ git switch -c $YOUR_BRANCH
$ echo $YOUR_CHANGES >> README.md
$ git commit README.md --message "$YOUR_COMMIT_MESSAGE"
$ gh-pr-upsert --title "$YOUR_PR_TITLE" --body "$YOUR_PR_BODY"
https://github.com/<YOUR_OWNER>/<YOUR_REPO>/pull/1
```

See `gh-pr-upsert --help` for command line options.

If a PR for `$YOUR_BRANCH` already exists then it'll be updated by
force-pushing.

If there are no changes on `$YOUR_BRANCH` compared to the base branch then any
existing PR for `$YOUR_BRANCH` will be closed: the PR apparently isn't needed
anymore.

`gh-pr-upsert` won't force-push any branches or close any PRs that contain
commits from anyone other than the current user (as reported by
`git config --get user.name` and `git config --get user.email`).

Requires [Git](https://git-scm.com/) and [GitHub CLI](https://cli.github.com/)
to be installed.

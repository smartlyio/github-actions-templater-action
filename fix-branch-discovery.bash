DEFAULT_BRANCH="$(gh api "/repos/${GITHUB_REPOSITORY}" | jq .default_branch)"
echo "ref: refs/remote/origin/${DEFAULT_BRANCH}" > .git/refs/remotes/origin/HEAD

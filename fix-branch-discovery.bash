DEFAULT_BRANCH="$(gh api "/repos/${INPUT_GITHUB_REPOSITORY}" | jq -r .default_branch)"
echo "ref: refs/remotes/origin/${DEFAULT_BRANCH}" > .git/refs/remotes/origin/HEAD

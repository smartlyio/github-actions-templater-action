git status
# Check for changes in .github/workflows
git_changes="$(git status --porcelain -- .github/workflows || true)"
# If the output is not empty, there are changes. Commit them
if [ -n "$git_changes" ]; then
    echo "Changes to workflows found!"
    BRANCH_NAME="${REPOSITORY_NAME}-github-actions-self-update"
    echo "Using branch: $BRANCH_NAME"
    git checkout -b "$BRANCH_NAME"

    echo "Adding workflows directory and making commit"
    git add .github/workflows/
    git commit -m "Adding workflow changes at $(date)"

    echo "Check if there is an existing branch and if the change set already exists in it."
    if [ -z "$(git diff "origin/$BRANCH_NAME" || echo "no branch")" ]; then
      echo "Seems to have no differences from existing branch!"
    else
      echo "Pushing the branch"
      git push --force-with-lease -u origin HEAD
    fi

    function pr_exists() {
        local repo="$1"
        local branch="$2"
        local PR_COUNT=
        PR_COUNT="$(gh api "repos/${repo}/pulls?state=open&head=smartlyio:${branch}" | jq '. | length')"
        [ "$PR_COUNT" -gt 0 ]
    }

    echo "Check if the PR already exists"
    if pr_exists "$GITHUB_REPOSITORY" "$BRANCH_NAME"; then
      echo "PR Exists already!"
      exit 0
    else
      echo "Make sure the labels exist"
      if [ -n "$PR_LABEL" ]; then
        if ! gh api "/repos/smartlyio/${REPOSITORY_NAME}/labels/${PR_LABEL}"; then
          gh api "/repos/smartlyio/${REPOSITORY_NAME}/labels" -X POST \
            -f "name=${PR_LABEL}" \
            -f "description=Do not create a release from this pull request"
        fi
      fi
      if ! gh api "/repos/smartlyio/${REPOSITORY_NAME}/labels/workflow-updater"; then
        gh api "/repos/smartlyio/${REPOSITORY_NAME}/labels" -X POST \
          -f "name=workflow-updater" \
          -f "color=ff2994" \
          -f "description=Automatically generated by workflow updater"
      fi
      echo "Create the PR!"
      gh pr create \
        --title "GitHub Actions Self Update for ${REPOSITORY_NAME}" \
        --body "These changes are generated by the GitHub Actions self updater. Remember to delete the branch!" \
        --reviewer fisherking,sjagoe,mhalmagiu \
        --label "${PR_LABEL:+${PR_LABEL},}workflow-updater"
      exit 0
    fi
else
    echo "No Changes Found."
    exit 0
fi

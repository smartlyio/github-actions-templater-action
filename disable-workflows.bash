if [ -z "$INPUT_DISABLE_WORKFLOWS_PREFIX" ]; then
    echo "No workflows configured for disabling"
    exit 0
fi

mapfile -t WORKFLOWS < <(find .github/workflows -type f -name "${INPUT_DISABLE_WORKFLOWS_PREFIX}*.yml")

for workflow in "${WORKFLOWS[@]}"; do
    echo "Disabling $workflow"
    yq e -i '.on = {"pull_request": {"types": ["locked"], "branches": ["workflow-renovate-canary-branch-should-never-exist"]}}' "$workflow"
done

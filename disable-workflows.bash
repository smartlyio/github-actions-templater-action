mapfile -t WORKFLOWS < <(find .github/workflows -name "${INPUT_DISABLE_WORKFLOWS_PREFIX}*")

for workflow in "${WORKFLOWS[@]}"; do
    echo "Disabling $workflow"
    yq e -i '.on = []' "$workflow"
done

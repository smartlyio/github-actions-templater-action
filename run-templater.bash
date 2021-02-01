REPOSITORY_NAME="$(echo "$INPUT_GITHUB_REPOSITORY" | awk -F / '{print $2}' | sed -e "s/:refs//")"
render_arg="--no-update"
local_render="${{ inputs.local-render }}"
if [[ "${local_render}" == "true" ]]; then
    render_arg="--local"
fi
docker pull "${{ inputs.templater-image-name }}"
docker run --hostname "workflow-update-${REPOSITORY_NAME}" --rm \
    --mount type=bind,src="$(pwd),dst=/devbox/workspace" \
    --mount type=bind,src="$(pwd)/${{ inputs.templates-location }},dst=/devbox/github-actions-templates" \
    "${{ inputs.templater-image-name }}" \
        render workflows "$render_arg"

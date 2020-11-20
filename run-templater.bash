docker pull "$DOCKER_IMAGE_NAME"
docker run --hostname "workflow-update-${REPOSITORY_NAME}" --rm \
    --mount type=bind,src="$(pwd),dst=/devbox/workspace" \
    --mount type=bind,src="$(pwd)/${TEMPLATES_LOCATION},dst=/devbox/github-actions-templates" \
    "$DOCKER_IMAGE_NAME" \
        render workflows --no-update

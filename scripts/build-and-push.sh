# Sample content for build-and-push.sh
#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Set your DockerHub username or organization
DOCKER_USER="sogumai"

# Define all services
SERVICES=(
  ocr-service
  docetl
  local-file-organizer
  anything-llm
  json-crack
  local-send
  pake
  kestra
  windmill
)

# Define the tag (can be 'latest' or derived from Git)
TAG="${1:-latest}"

for SERVICE in "${SERVICES[@]}"; do
  IMAGE_NAME="${DOCKER_USER}/${SERVICE}:${TAG}"
  echo "📦 Building $SERVICE..."
  docker build -t "$IMAGE_NAME" "./services/$SERVICE"

  echo "📤 Pushing $IMAGE_NAME..."
  docker push "$IMAGE_NAME"
done

echo "✅ All images built and pushed successfully with tag: $TAG"

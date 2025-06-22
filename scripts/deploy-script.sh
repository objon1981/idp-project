#!/bin/bash
set -e

# === CONFIGURATION ===
DOCKER_USER="sogumai"
TAG="${2:-latest}"
CHART_NAME="sogum-umbrella"
RELEASE_NAME="sogum-idp"
CHART_PATH="./charts/$CHART_NAME"
NAMESPACE="sogum-idp"
HELM_DEPLOYMENTS=("sogum-idp-kestra" "sogum-idp-windmill")
SERVICES=(ocr-service docetl local-file-organizer anything-llm json-crack local-send spake kestra windmill)

# === HELP MESSAGE ===
usage() {
  echo "Usage: $0 [--init-cluster] [--build-push] [--docker] [--helm] [--tag <tag>]"
  echo ""
  echo "  --init-cluster     Initialize Kubernetes namespace, secrets, and ingress"
  echo "  --build-push       Build and push Docker images to Docker Hub"
  echo "  --docker           Deploy local microservices using Docker Compose"
  echo "  --helm             Deploy to Kubernetes using Helm"
  echo "  --tag <tag>        Optional image tag (default: latest)"
  echo ""
  exit 1
}

# === PARSE FLAGS ===
INIT_CLUSTER=false
BUILD_PUSH=false
DOCKER_DEPLOY=false
HELM_DEPLOY=false

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --init-cluster) INIT_CLUSTER=true ;;
    --build-push) BUILD_PUSH=true ;;
    --docker) DOCKER_DEPLOY=true ;;
    --helm) HELM_DEPLOY=true ;;
    --tag) TAG="$2"; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown parameter passed: $1"; usage ;;
  esac
  shift
done

# === STEP 1: Init Kubernetes Cluster ===
if $INIT_CLUSTER; then
  echo "🚀 Initializing Kubernetes cluster..."

  echo "🔧 Creating namespace '$NAMESPACE'..."
  kubectl get namespace "$NAMESPACE" || kubectl create namespace "$NAMESPACE"

  if [ -f k8s/secrets.yaml ]; then
    echo "🔐 Applying secrets..."
    kubectl apply -f k8s/secrets.yaml -n "$NAMESPACE"
  else
    echo "⚠️ No secrets.yaml found. Skipping..."
  fi

  echo "🌐 Installing NGINX Ingress controller..."
  helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
  helm repo update
  helm upgrade --install nginx ingress-nginx/ingress-nginx \
    --namespace ingress-nginx --create-namespace
fi

# === STEP 2: Build and Push Docker Images ===
if $BUILD_PUSH; then
  echo "📦 Building and pushing Docker images..."
  for SERVICE in "${SERVICES[@]}"; do
    IMAGE_NAME="${DOCKER_USER}/${SERVICE}:${TAG}"
    echo "🔨 Building $SERVICE..."
    docker build -t "$IMAGE_NAME" "./services/$SERVICE"
    echo "🚀 Pushing $IMAGE_NAME..."
    docker push "$IMAGE_NAME"
  done
  echo "✅ All images pushed with tag: $TAG"
fi

# === STEP 3: Deploy Local Microservices with Docker Compose ===
if $DOCKER_DEPLOY; then
  echo "🧱 Deploying local Docker services..."

  mkdir -p data/{input,output,watched,organized} logs monitoring

  if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please configure your .env file!"
    exit 1
  fi

  docker-compose build --no-cache
  docker-compose up -d

  echo "✅ Local services deployed!"
  echo "📊 Grafana: http://localhost:3010 (admin/admin123)"
  echo "📈 Prometheus: http://localhost:9090"
  echo "🤖 Anything-LLM: http://localhost:3001"
  echo "🔍 OCR Service: http://localhost:5001"
  echo "📁 Local Send: http://localhost:5000"

  echo "⏳ Waiting for services..."
  sleep 30
  docker-compose ps
fi

# === STEP 4: Deploy to Kubernetes via Helm ===
if $HELM_DEPLOY; then
  echo "🚢 Deploying Helm chart..."

  echo "📦 Updating Helm dependencies..."
  helm dependency update "$CHART_PATH"

  echo "🔁 Running Helm upgrade/install..."
  helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" -n "$NAMESPACE"

  echo "⏳ Waiting for Helm deployments to roll out..."
  for DEPLOY in "${HELM_DEPLOYMENTS[@]}"; do
    kubectl rollout status deployment/"$DEPLOY" -n "$NAMESPACE" || {
      echo "❌ Rollout failed for $DEPLOY"
      exit 1
    }
  done

  echo "✅ Helm deployment completed."
fi

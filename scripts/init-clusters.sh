# Sample content for init-cluster.sh
#!/bin/bash

set -e

NAMESPACE="sogum-idp"
CHART_NAME="sogum-umbrella"
RELEASE_NAME="sogum-idp"
CHART_PATH="./charts/$CHART_NAME"

echo "🚀 Initializing Kubernetes cluster for $CHART_NAME..."

# Step 1: Create namespace if it doesn't exist
echo "🔧 Creating namespace '$NAMESPACE'..."
kubectl get namespace $NAMESPACE || kubectl create namespace $NAMESPACE

# Step 2: Apply required secrets (if you have a file for that)
if [ -f k8s/secrets.yaml ]; then
  echo "🔐 Applying secrets from k8s/secrets.yaml..."
  kubectl apply -f k8s/secrets.yaml -n $NAMESPACE
else
  echo "⚠️ No secrets.yaml file found. Skipping secret creation."
fi

# Step 3: Install ingress controller (optional)
echo "🌐 Installing NGINX Ingress controller..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

# Step 4: Setup local Helm dependencies
echo "📦 Updating Helm dependencies..."
helm dependency update $CHART_PATH

# Step 5: Deploy umbrella chart
echo "🚢 Deploying Helm chart '$CHART_NAME' as release '$RELEASE_NAME'..."
helm upgrade --install $RELEASE_NAME $CHART_PATH --namespace $NAMESPACE

echo "✅ Cluster initialization complete!"

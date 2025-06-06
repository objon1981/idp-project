#!/bin/bash

# === CONFIGURATION ===
CHART_NAME="sogum-idp"
CHART_DIR="/opt/sogum-umbrella"
VALUES_FILE="values.yaml"
NAMESPACE="default"  # Change to your specific namespace if needed

# === DEPLOYMENT LOGIC ===

echo ">>> Navigating to Helm chart directory..."
cd "$CHART_DIR" || {
  echo "❌ Failed to change directory to $CHART_DIR"
  exit 1
}

echo ">>> Updating Helm dependencies..."
helm dependency update || {
  echo "❌ Failed to update Helm dependencies"
  exit 1
}

echo ">>> Performing Helm upgrade/install..."
helm upgrade --install "$CHART_NAME" . -f "$VALUES_FILE" --namespace "$NAMESPACE" || {
  echo "❌ Helm upgrade failed"
  exit 1
}

echo ">>> Waiting for deployments to roll out..."
DEPLOYMENTS=("sogum-idp-kestra" "sogum-idp-windmill")  # Add more as needed

for deployment in "${DEPLOYMENTS[@]}"; do
  echo "⏳ Checking rollout status for $deployment..."
  kubectl rollout status deployment/"$deployment" --namespace "$NAMESPACE" || {
    echo "❌ Rollout failed for $deployment"
    exit 1
  }
done

echo "✅ Deployment completed successfully."

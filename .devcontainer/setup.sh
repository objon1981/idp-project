#!/bin/bash

set -e

echo "🛠 Updating system & installing tools..."
apt-get update && apt-get install -y sudo curl apt-transport-https gnupg

echo "🐳 Checking Docker group membership..."
id vscode || true
groups vscode || true

echo "📦 Installing Minikube..."
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install -o root -g root -m 0755 minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64

echo "☸️ Installing kubectl..."
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

echo "⎈ Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

echo "🐍 Installing Python packages..."
pip install --upgrade pip
pip install pandas numpy opencv-python pytesseract requests fastapi uvicorn aiofiles pyyaml python-dotenv langchain openai

echo "✅ Dev container setup complete!"

#!/bin/bash

set -e

echo "Setting up amoneyplan Kubernetes development environment"

# Create kind cluster
echo "Creating kind cluster..."
kind create cluster --config=kind-config.yaml --name amoneyplan

# Build Docker image for backend
echo "Building backend Docker image..."
cd ../backend
docker build -t amoneyplan-backend:latest .

# Load image into kind
echo "Loading image into kind cluster..."
kind load docker-image amoneyplan-backend:latest --name amoneyplan

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
cd ../infra
kubectl apply -f namespace.yaml
kubectl apply -f postgres-config.yaml
kubectl apply -f postgres-pvc.yaml
kubectl apply -f postgres.yaml

echo "Waiting for PostgreSQL to be ready..."
kubectl wait --namespace amoneyplan \
  --for=condition=ready pod \
  --selector=app=postgres \
  --timeout=90s

kubectl apply -f backend.yaml

echo "Setup complete!"
echo "You can access your application at: http://localhost:8000/graphql/"
echo ""
echo "To view the status of your pods, run:"
echo "  kubectl get pods -n amoneyplan"
echo ""
echo "To view the logs of your backend service, run:"
echo "  kubectl logs -n amoneyplan deployment/backend"
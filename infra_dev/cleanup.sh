#!/bin/bash

echo "Cleaning up amoneyplan Kubernetes development environment"

# Delete kind cluster
echo "Deleting kind cluster..."
kind delete cluster --name amoneyplan

echo "Cleanup complete!"
#!/bin/bash

# Display usage information if no arguments are provided
if [ "$#" -eq 0 ]; then
  echo "Usage: ./logs.sh [backend|postgres|all]"
  echo
  echo "Options:"
  echo "  backend   - View logs from the backend service"
  echo "  postgres  - View logs from the PostgreSQL database"
  echo "  all       - View logs from all pods (using stern if installed)"
  exit 1
fi

# Check which component to show logs for
case "$1" in
  backend)
    echo "Following backend logs (Ctrl+C to exit)..."
    kubectl -n amoneyplan logs -f deployment/backend
    ;;
  postgres)
    echo "Following PostgreSQL logs (Ctrl+C to exit)..."
    kubectl -n amoneyplan logs -f deployment/postgres
    ;;
  all)
    # Check if stern is installed
    if command -v stern &> /dev/null; then
      echo "Following all logs with stern (Ctrl+C to exit)..."
      stern -n amoneyplan ".*"
    else
      echo "Following all logs (Ctrl+C to exit)..."
      kubectl -n amoneyplan logs -f --all-containers=true --selector='app in (backend, postgres)'
    fi
    ;;
  *)
    echo "Invalid option: $1"
    echo "Usage: ./logs.sh [backend|postgres|all]"
    exit 1
    ;;
esac
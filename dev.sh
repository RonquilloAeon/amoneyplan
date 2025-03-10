#!/bin/bash

# Show help message if no arguments or help command
if [ "$#" -eq 0 ] || [ "$1" = "help" ]; then
    echo "AMoneyPlan Development Helper"
    echo "============================"
    echo
    echo "This script helps manage your local development environment."
    echo "It's a wrapper around the Terraform configuration in infra_dev/terraform."
    echo
    echo "Development commands:"
    echo "  reload    - Restart the backend pod (use when file changes aren't detected)"
    echo "  backend   - Run backend-related commands via tf.sh"
    echo "  frontend  - Run frontend-related commands via pnpm"
    echo
    echo "Available commands (from tf.sh):"
    echo "--------------------------------"
    cd infra_dev/terraform && ./tf.sh help
    exit 0
fi

case "$1" in
    "backend")
        shift  # Remove the first argument
        cd infra_dev/terraform && ./tf.sh "$@"
        ;;
    "frontend")
        shift  # Remove the first argument
        cd frontend && pnpm "$@"
        ;;
    *)
        cd infra_dev/terraform && ./tf.sh "$@"
        ;;
esac

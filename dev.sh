#!/bin/bash

# Show help message if no arguments or help command
if [ "$#" -eq 0 ] || [ "$1" = "help" ]; then
    echo "AMoneyPlan Development Helper"
    echo "============================"
    echo
    echo "This script helps manage your local development environment."
    echo "It's a wrapper around the Terraform configuration in infra/terraform."
    echo
    echo "Development commands:"
    echo "  reload    - Restart the backend pod (use when file changes aren't detected)"
    echo
    echo "Available commands (from tf.sh):"
    echo "--------------------------------"
    cd infra/terraform && ./tf.sh help
    exit 0
fi

# Change to the Terraform directory and execute tf.sh with all arguments
cd infra_dev/terraform && ./tf.sh "$@"
